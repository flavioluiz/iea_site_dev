import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";
import test from "node:test";

import { handleRequest } from "../src/index.js";

const env = {
  GITHUB_OAUTH_ID: "client-id",
  GITHUB_OAUTH_SECRET: "test-secret-that-is-long-enough",
  OAUTH_CALLBACK_URL: "https://iea-decap-oauth.example.workers.dev/callback",
  ALLOWED_ORIGINS: "https://flavioluiz.github.io,http://localhost:1313",
  ALLOWED_GITHUB_USERS: "flavioluiz,editor-iea",
};
const now = () => Date.parse("2026-08-14T12:00:00Z");

async function begin(siteId = "flavioluiz.github.io") {
  const response = await handleRequest(
    new Request(`https://iea-decap-oauth.example.workers.dev/auth?provider=github&site_id=${encodeURIComponent(siteId)}`),
    env,
    { crypto: webcrypto, now },
  );
  const authorization = new URL(response.headers.get("Location"));
  return {
    response,
    state: authorization.searchParams.get("state"),
    cookie: response.headers.get("Set-Cookie").split(";", 1)[0],
    authorization,
  };
}

function githubFetch(login = "flavioluiz", tokenStatus = 200) {
  return async (url) => {
    if (String(url).includes("access_token")) {
      return new Response(
        JSON.stringify(tokenStatus === 200 ? { access_token: "token-value" } : { error: "bad_verification_code" }),
        { status: tokenStatus, headers: { "Content-Type": "application/json" } },
      );
    }
    if (String(url).endsWith("/user")) {
      return Response.json({ login });
    }
    throw new Error(`Unexpected URL: ${url}`);
  };
}

async function callback(flow, options = {}) {
  return handleRequest(
    new Request(
      `https://iea-decap-oauth.example.workers.dev/callback?code=temporary-code&state=${encodeURIComponent(options.state || flow.state)}`,
      { headers: { Cookie: flow.cookie } },
    ),
    env,
    { crypto: webcrypto, now, fetch: options.fetch || githubFetch() },
  );
}

test("/auth rejects providers other than GitHub", async () => {
  const response = await handleRequest(
    new Request("https://iea-decap-oauth.example.workers.dev/auth?provider=gitlab&site_id=flavioluiz.github.io"),
    env,
    { crypto: webcrypto, now },
  );
  assert.equal(response.status, 400);
});

test("/auth rejects an origin outside the allowlist", async () => {
  const response = await handleRequest(
    new Request("https://iea-decap-oauth.example.workers.dev/auth?provider=github&site_id=evil.example"),
    env,
    { crypto: webcrypto, now },
  );
  assert.equal(response.status, 403);
});

test("/auth creates a short secure state cookie and PKCE challenge", async () => {
  const flow = await begin();
  assert.equal(flow.response.status, 302);
  assert.match(flow.response.headers.get("Set-Cookie"), /Secure; HttpOnly; SameSite=Lax/u);
  assert.equal(flow.authorization.searchParams.get("code_challenge_method"), "S256");
  assert.ok(flow.authorization.searchParams.get("code_challenge"));
  assert.equal(flow.authorization.searchParams.get("redirect_uri"), env.OAUTH_CALLBACK_URL);
});

test("callback rejects a missing code", async () => {
  const response = await handleRequest(
    new Request("https://iea-decap-oauth.example.workers.dev/callback?state=x"),
    env,
    { crypto: webcrypto, now },
  );
  assert.equal(response.status, 400);
});

test("callback rejects an invalid state before contacting GitHub", async () => {
  const flow = await begin();
  let contacted = false;
  const response = await callback(flow, { state: "attacker-state", fetch: async () => { contacted = true; } });
  assert.equal(response.status, 400);
  assert.equal(contacted, false);
});

test("callback returns a safe error when GitHub rejects the code", async () => {
  const flow = await begin();
  const response = await callback(flow, { fetch: githubFetch("flavioluiz", 401) });
  assert.equal(response.status, 502);
  assert.doesNotMatch(await response.text(), /token-value/u);
});

test("callback rejects a GitHub login outside the user allowlist", async () => {
  const flow = await begin();
  const response = await callback(flow, { fetch: githubFetch("not-authorized") });
  assert.equal(response.status, 403);
  assert.match(await response.text(), /não autorizada/u);
});

test("callback sends the token only to the exact CMS origin", async () => {
  const flow = await begin();
  const response = await callback(flow);
  const body = await response.text();
  assert.equal(response.status, 200);
  assert.match(body, /token-value/u);
  assert.match(body, /https:\/\/flavioluiz\.github\.io/u);
  assert.doesNotMatch(body, /postMessage\([^)]*,\s*["']\*["']/u);
  assert.match(response.headers.get("Content-Security-Policy"), /script-src 'nonce-/u);
  assert.equal(response.headers.get("Cache-Control"), "no-store, max-age=0");
});
