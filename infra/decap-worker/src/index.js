const COOKIE_NAME = "decap_oauth_state";
const STATE_TTL_SECONDS = 10 * 60;
const GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize";
const GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token";
const GITHUB_USER_URL = "https://api.github.com/user";

const encoder = new TextEncoder();

function commonHeaders(contentType = "text/plain; charset=utf-8") {
  return {
    "Cache-Control": "no-store, max-age=0",
    "Content-Type": contentType,
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
  };
}

function textResponse(message, status = 200, extraHeaders = {}) {
  return new Response(message, {
    status,
    headers: { ...commonHeaders(), ...extraHeaders },
  });
}

function splitList(value) {
  return new Set(
    String(value || "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
  );
}

function bytesToBase64Url(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/u, "");
}

function stringToBase64Url(value) {
  return bytesToBase64Url(encoder.encode(value));
}

function base64UrlToString(value) {
  const normalized = value.replaceAll("-", "+").replaceAll("_", "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
  return decodeURIComponent(
    Array.from(atob(padded), (character) =>
      `%${character.charCodeAt(0).toString(16).padStart(2, "0")}`,
    ).join(""),
  );
}

function randomBase64Url(length, cryptoImpl) {
  const bytes = new Uint8Array(length);
  cryptoImpl.getRandomValues(bytes);
  return bytesToBase64Url(bytes);
}

async function hmac(value, secret, cryptoImpl) {
  const key = await cryptoImpl.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await cryptoImpl.subtle.sign("HMAC", key, encoder.encode(value));
  return bytesToBase64Url(new Uint8Array(signature));
}

async function signPayload(payload, secret, cryptoImpl) {
  const encoded = stringToBase64Url(JSON.stringify(payload));
  return `${encoded}.${await hmac(encoded, secret, cryptoImpl)}`;
}

async function verifyPayload(token, secret, cryptoImpl) {
  const [encoded, suppliedSignature, extra] = String(token || "").split(".");
  if (!encoded || !suppliedSignature || extra) return null;
  const expectedSignature = await hmac(encoded, secret, cryptoImpl);
  if (expectedSignature.length !== suppliedSignature.length) return null;
  let difference = 0;
  for (let index = 0; index < expectedSignature.length; index += 1) {
    difference |= expectedSignature.charCodeAt(index) ^ suppliedSignature.charCodeAt(index);
  }
  if (difference !== 0) return null;
  try {
    return JSON.parse(base64UrlToString(encoded));
  } catch {
    return null;
  }
}

async function pkceChallenge(verifier, cryptoImpl) {
  const digest = await cryptoImpl.subtle.digest("SHA-256", encoder.encode(verifier));
  return bytesToBase64Url(new Uint8Array(digest));
}

function cookieValue(request, name) {
  const cookieHeader = request.headers.get("Cookie") || "";
  for (const item of cookieHeader.split(";")) {
    const separator = item.indexOf("=");
    if (separator === -1) continue;
    if (item.slice(0, separator).trim() === name) return item.slice(separator + 1).trim();
  }
  return "";
}

function stateCookie(value, maxAge = STATE_TTL_SECONDS) {
  return `${COOKIE_NAME}=${value}; Path=/callback; Max-Age=${maxAge}; Secure; HttpOnly; SameSite=Lax`;
}

function requiredCallbackUrl(env) {
  const callback = new URL(env.OAUTH_CALLBACK_URL);
  if (callback.protocol !== "https:" || callback.pathname !== "/callback" || callback.search) {
    throw new Error("OAUTH_CALLBACK_URL must be a fixed HTTPS URL ending in /callback");
  }
  return callback.toString();
}

function originForSiteId(siteId, allowedOrigins) {
  if (!siteId) return null;
  let requestedOrigin = null;
  try {
    requestedOrigin = new URL(siteId).origin;
  } catch {
    for (const origin of allowedOrigins) {
      try {
        if (new URL(origin).hostname === siteId) requestedOrigin = origin;
      } catch {
        return null;
      }
    }
  }
  return requestedOrigin && allowedOrigins.has(requestedOrigin) ? requestedOrigin : null;
}

function callbackHtml({ origin, status, token = "", message = "" }, nonce) {
  const payload = status === "success" ? { token } : { message };
  const authorization = `authorization:github:${status}:${JSON.stringify(payload)}`;
  const script = `
    (() => {
      const targetOrigin = ${JSON.stringify(origin)};
      const receiveMessage = (event) => {
        if (event.origin !== targetOrigin || event.source !== window.opener) return;
        window.opener.postMessage(${JSON.stringify(authorization)}, targetOrigin);
        window.removeEventListener("message", receiveMessage, false);
      };
      window.addEventListener("message", receiveMessage, false);
      window.opener.postMessage("authorizing:github", targetOrigin);
    })();`;
  return `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="referrer" content="no-referrer"><title>Autorizando editor</title></head>
<body><p>${status === "success" ? "Autorização concluída. Esta janela será fechada." : "Não foi possível autorizar o editor."}</p>
<script nonce="${nonce}">${script}</script></body></html>`;
}

function htmlResponse(options, statusCode, nonce, clearCookie = true) {
  const headers = {
    ...commonHeaders("text/html; charset=utf-8"),
    "Content-Security-Policy": `default-src 'none'; script-src 'nonce-${nonce}'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`,
  };
  if (clearCookie) headers["Set-Cookie"] = stateCookie("", 0);
  return new Response(callbackHtml(options, nonce), { status: statusCode, headers });
}

async function exchangeCode(code, verifier, env, fetchImpl) {
  const response = await fetchImpl(GITHUB_TOKEN_URL, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/x-www-form-urlencoded",
      "User-Agent": "iea-decap-oauth-worker",
    },
    body: new URLSearchParams({
      client_id: env.GITHUB_OAUTH_ID,
      client_secret: env.GITHUB_OAUTH_SECRET,
      code,
      redirect_uri: requiredCallbackUrl(env),
      code_verifier: verifier,
    }),
  });
  if (!response.ok) throw new Error("GitHub token endpoint rejected the request");
  const body = await response.json();
  if (!body.access_token || body.error) throw new Error("GitHub did not return an access token");
  return body.access_token;
}

async function githubLogin(token, fetchImpl) {
  const response = await fetchImpl(GITHUB_USER_URL, {
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${token}`,
      "User-Agent": "iea-decap-oauth-worker",
      "X-GitHub-Api-Version": "2022-11-28",
    },
  });
  if (!response.ok) throw new Error("GitHub user endpoint rejected the token");
  const body = await response.json();
  if (!body.login) throw new Error("GitHub user response has no login");
  return String(body.login).toLowerCase();
}

async function handleAuth(url, request, env, deps) {
  if (request.method !== "GET") return textResponse("Method not allowed", 405, { Allow: "GET" });
  if (url.searchParams.get("provider") !== "github") return textResponse("Invalid provider", 400);

  const allowedOrigins = splitList(env.ALLOWED_ORIGINS);
  const origin = originForSiteId(url.searchParams.get("site_id"), allowedOrigins);
  if (!origin) return textResponse("Origin is not authorized", 403);

  const state = randomBase64Url(32, deps.crypto);
  const verifier = randomBase64Url(64, deps.crypto);
  const challenge = await pkceChallenge(verifier, deps.crypto);
  const payload = await signPayload(
    { state, verifier, origin, expiresAt: deps.now() + STATE_TTL_SECONDS * 1000 },
    env.GITHUB_OAUTH_SECRET,
    deps.crypto,
  );
  const authorizationUrl = new URL(GITHUB_AUTHORIZE_URL);
  authorizationUrl.search = new URLSearchParams({
    client_id: env.GITHUB_OAUTH_ID,
    redirect_uri: requiredCallbackUrl(env),
    scope: "public_repo",
    state,
    code_challenge: challenge,
    code_challenge_method: "S256",
  }).toString();

  return new Response(null, {
    status: 302,
    headers: {
      ...commonHeaders(),
      Location: authorizationUrl.toString(),
      "Set-Cookie": stateCookie(payload),
    },
  });
}

async function handleCallback(url, request, env, deps) {
  if (request.method !== "GET") return textResponse("Method not allowed", 405, { Allow: "GET" });
  if (url.searchParams.has("provider") && url.searchParams.get("provider") !== "github") {
    return textResponse("Invalid provider", 400);
  }
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  if (!code || !state) return textResponse("Missing OAuth code or state", 400);

  const payload = await verifyPayload(cookieValue(request, COOKIE_NAME), env.GITHUB_OAUTH_SECRET, deps.crypto);
  if (!payload || payload.state !== state || payload.expiresAt < deps.now()) {
    return textResponse("Invalid or expired OAuth state", 400, { "Set-Cookie": stateCookie("", 0) });
  }
  const allowedOrigins = splitList(env.ALLOWED_ORIGINS);
  if (!allowedOrigins.has(payload.origin)) {
    return textResponse("Origin is no longer authorized", 403, { "Set-Cookie": stateCookie("", 0) });
  }
  const nonce = randomBase64Url(18, deps.crypto);
  try {
    const token = await exchangeCode(code, payload.verifier, env, deps.fetch);
    const login = await githubLogin(token, deps.fetch);
    const allowedUsers = new Set([...splitList(env.ALLOWED_GITHUB_USERS)].map((item) => item.toLowerCase()));
    if (!allowedUsers.size || !allowedUsers.has(login)) {
      return htmlResponse(
        { origin: payload.origin, status: "error", message: "Conta GitHub não autorizada." },
        403,
        nonce,
      );
    }
    return htmlResponse({ origin: payload.origin, status: "success", token }, 200, nonce);
  } catch {
    return htmlResponse(
      { origin: payload.origin, status: "error", message: "O GitHub recusou a autorização." },
      502,
      nonce,
    );
  }
}

export async function handleRequest(request, env, overrides = {}) {
  const deps = {
    fetch: overrides.fetch || fetch,
    crypto: overrides.crypto || crypto,
    now: overrides.now || Date.now,
  };
  const url = new URL(request.url);
  try {
    if (url.pathname === "/auth") return await handleAuth(url, request, env, deps);
    if (url.pathname === "/callback") return await handleCallback(url, request, env, deps);
    if (url.pathname === "/health") return textResponse("ok");
    return textResponse("Not found", 404);
  } catch {
    return textResponse("OAuth service configuration error", 500);
  }
}

export default {
  fetch(request, env) {
    return handleRequest(request, env);
  },
};
