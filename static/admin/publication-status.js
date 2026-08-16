(() => {
  const STORAGE_KEY = "iea-publication-status-v1";
  const DEPLOY_RUNS_URL = "https://api.github.com/repos/flavioluiz/iea_site_dev/actions/workflows/deploy.yml/runs?branch=main&per_page=5";
  const WORKFLOW_URL = "https://github.com/flavioluiz/iea_site_dev/actions/workflows/deploy.yml";
  const POLL_INTERVAL_MS = 20000;
  const CONFIRMATION_TIMEOUT_MS = 2 * 60 * 1000;
  const ACTIVE_MAX_AGE_MS = 30 * 60 * 1000;
  const COMPLETED_MAX_AGE_MS = 15 * 60 * 1000;
  let timer = null;

  const readState = () => {
    try {
      const value = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "null");
      if (!value || !Number.isFinite(value.startedAt)) return null;
      const referenceTime = value.completedAt || value.startedAt;
      const maxAge = value.phase === "published" ? COMPLETED_MAX_AGE_MS : ACTIVE_MAX_AGE_MS;
      if (Date.now() - referenceTime > maxAge) {
        try { window.localStorage.removeItem(STORAGE_KEY); } catch (storageError) { /* aviso apenas */ }
        return null;
      }
      return value;
    } catch (error) {
      try { window.localStorage.removeItem(STORAGE_KEY); } catch (storageError) { /* aviso apenas */ }
      return null;
    }
  };

  const writeState = state => {
    try { window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (error) { /* aviso apenas */ }
    render(state);
  };

  const entryDetails = entry => {
    if (!entry || typeof entry.get !== "function") return {};
    const data = entry.get("data");
    const collection = entry.get("collection") || "";
    const slug = entry.get("slug") || "";
    let title = "alteração";
    if (data && typeof data.getIn === "function") {
      title = data.getIn(["pagina", "titulo", "pt"])
        || data.get("titulo_pt")
        || data.get("nome")
        || data.get("title")
        || data.get("id")
        || title;
    }
    const siteUrl = collection === "paginas" && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)
      ? new URL(`../pt/${slug}/`, window.location.href).href
      : new URL("../pt/", window.location.href).href;
    return { collection, slug, title: String(title), siteUrl };
  };

  const notice = document.createElement("aside");
  notice.id = "publication-status";
  notice.setAttribute("role", "status");
  notice.setAttribute("aria-live", "polite");
  notice.style.cssText = "display:none;position:fixed;left:50%;top:14px;transform:translateX(-50%);z-index:100001;width:min(620px,calc(100% - 28px));padding:14px 46px 14px 17px;border:1px solid #b8c7da;border-left:6px solid #176b46;border-radius:11px;background:white;box-shadow:0 8px 28px #1720333d;color:#172033;font:14px/1.45 system-ui";
  document.body.appendChild(notice);

  const phaseContent = state => {
    if (state.phase === "accepting") {
      return {
        title: "Enviando a publicação…",
        detail: "Aguarde a confirmação do editor. Ainda não feche esta página.",
        color: "#9a5b13"
      };
    }
    if (state.phase === "waiting") {
      return {
        title: "Alteração aceita — preparando o site",
        detail: "Ela já saiu da revisão. O site está entrando na fila de publicação; normalmente leva de um a dois minutos.",
        color: "#176b46"
      };
    }
    if (state.phase === "deploying") {
      return {
        title: "Publicação em andamento…",
        detail: "O site está sendo reconstruído. Você pode continuar usando o editor enquanto aguarda.",
        color: "#176b46"
      };
    }
    if (state.phase === "published") {
      const completed = new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" }).format(new Date(state.completedAt));
      return {
        title: "Publicação concluída",
        detail: `${state.title || "A alteração"} já está no site desde ${completed}.`,
        color: "#176b46"
      };
    }
    if (state.phase === "unconfirmed") {
      return {
        title: "Publicação não confirmada",
        detail: "O editor não confirmou o envio. Se apareceu uma mensagem de erro, volte a Rascunhos e revisão antes de tentar novamente.",
        color: "#b42318"
      };
    }
    return {
      title: "A publicação precisa de atenção",
      detail: "A alteração foi aceita, mas a atualização do site não terminou. Um mantenedor deve verificar o processo.",
      color: "#b42318"
    };
  };

  const render = state => {
    notice.replaceChildren();
    if (!state) {
      notice.style.display = "none";
      return;
    }
    const content = phaseContent(state);
    const heading = document.createElement("strong");
    const detail = document.createElement("span");
    const actions = document.createElement("span");
    const primaryLink = document.createElement("a");
    const close = document.createElement("button");

    heading.textContent = content.title;
    heading.style.cssText = "display:block;margin-bottom:2px;font-size:15px";
    detail.textContent = content.detail;
    actions.style.cssText = "display:flex;flex-wrap:wrap;gap:12px;margin-top:7px";
    primaryLink.href = state.phase === "published" ? state.siteUrl : (state.runUrl || WORKFLOW_URL);
    primaryLink.target = "_blank";
    primaryLink.rel = "noopener noreferrer";
    primaryLink.textContent = state.phase === "published" ? "Abrir no site" : "Acompanhar publicação";
    primaryLink.style.cssText = "color:#173b73;font-weight:750";
    close.type = "button";
    close.setAttribute("aria-label", "Fechar aviso");
    close.textContent = "×";
    close.style.cssText = "position:absolute;right:10px;top:9px;width:30px;height:30px;border:0;border-radius:999px;background:#eef2f7;color:#172033;font:20px/1 system-ui;cursor:pointer";
    close.addEventListener("click", () => {
      try { window.localStorage.removeItem(STORAGE_KEY); } catch (error) { /* aviso apenas */ }
      notice.style.display = "none";
      if (timer) window.clearTimeout(timer);
    });

    actions.appendChild(primaryLink);
    notice.append(heading, detail, actions, close);
    notice.style.borderLeftColor = content.color;
    notice.style.display = "block";
  };

  const schedulePoll = () => {
    if (timer) window.clearTimeout(timer);
    timer = window.setTimeout(checkDeploy, POLL_INTERVAL_MS);
  };

  const scheduleConfirmationTimeout = state => {
    const remaining = Math.max(0, CONFIRMATION_TIMEOUT_MS - (Date.now() - state.startedAt));
    window.setTimeout(() => {
      const current = readState();
      if (!current || current.phase !== "accepting") return;
      current.phase = "unconfirmed";
      writeState(current);
    }, remaining);
  };

  const checkDeploy = async () => {
    const state = readState();
    if (!state || !["waiting", "deploying"].includes(state.phase)) return;
    try {
      const response = await fetch(DEPLOY_RUNS_URL, {
        headers: { Accept: "application/vnd.github+json" },
        referrerPolicy: "no-referrer"
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      const threshold = (state.acceptedAt || state.startedAt) - 10000;
      const run = (payload.workflow_runs || []).find(item => Date.parse(item.created_at) >= threshold);
      if (!run) {
        render(state);
        schedulePoll();
        return;
      }
      state.runUrl = run.html_url || WORKFLOW_URL;
      if (run.status !== "completed") {
        state.phase = "deploying";
        writeState(state);
        schedulePoll();
        return;
      }
      if (run.conclusion === "success") {
        state.phase = "published";
        state.completedAt = Date.parse(run.updated_at) || Date.now();
      } else {
        state.phase = "failed";
        state.completedAt = Date.now();
      }
      writeState(state);
    } catch (error) {
      render(state);
      schedulePoll();
    }
  };

  if (window.CMS && typeof window.CMS.registerEventListener === "function") {
    window.CMS.registerEventListener({
      name: "prePublish",
      handler: ({ entry }) => {
        try {
          const state = { ...entryDetails(entry), phase: "accepting", startedAt: Date.now() };
          writeState(state);
          scheduleConfirmationTimeout(state);
        } catch (error) { /* o aviso nunca pode impedir a publicação */ }
      }
    });
    window.CMS.registerEventListener({
      name: "postPublish",
      handler: ({ entry }) => {
        try {
          const previous = readState();
          const state = {
            ...(previous || {}),
            ...entryDetails(entry),
            phase: "waiting",
            startedAt: previous && previous.startedAt || Date.now(),
            acceptedAt: Date.now()
          };
          writeState(state);
          checkDeploy();
        } catch (error) { /* o aviso nunca pode impedir a publicação */ }
      }
    });
  }

  const savedState = readState();
  render(savedState);
  if (savedState && ["waiting", "deploying"].includes(savedState.phase)) checkDeploy();
  if (savedState && savedState.phase === "accepting") scheduleConfirmationTimeout(savedState);
})();
