(() => {
  const roleMeta = {
    grupo: { icon: "📁", label: "Seção do menu", help: "Organiza os itens abaixo" },
    pagina_editavel: { icon: "📄", label: "Página no menu", help: "Página criada no painel" },
    pagina_estrutural: { icon: "📄", label: "Página no menu", help: "Página existente do site" },
    link_externo: { icon: "🔗", label: "Link externo", help: "Abre outro site" },
    categoria: { icon: "🏷️", label: "Título de categoria", help: "Organiza o submenu" },
    separador: { icon: "", label: "Separador", help: "Espaço visual" },
    raiz: { icon: "", label: "Raiz técnica", help: "" }
  };
  const originMeta = {
    markdown: { icon: "📝", label: "Markdown completo", action: "Editar página em Markdown" },
    markdown_lista: { icon: "📝", label: "Markdown + páginas filhas", action: "Editar texto em Markdown" },
    markdown_secao: { icon: "📝", label: "Seção de página Markdown", action: "Editar página em Markdown" },
    dados_markdown: { icon: "🗂", label: "Markdown + dados estruturados", action: "Editar texto em Markdown" },
    template_markdown: { icon: "🧱", label: "Template especial + Markdown", action: "Editar textos" },
    importada: { icon: "⚙️", label: "Markdown + dados importados", action: "Editar introdução" },
    menu: { icon: "📁", label: "Somente menu", action: "" },
    externo: { icon: "🔗", label: "Destino externo", action: "" },
    organizacao: { icon: "🏷️", label: "Organização do menu", action: "" },
    desconhecida: { icon: "🧩", label: "Template ou dados", action: "Editar conteúdo" }
  };

  const tree = document.getElementById("map-tree");
  const status = document.getElementById("map-status");
  const hiddenToggle = document.getElementById("show-hidden");
  const technicalToggle = document.getElementById("show-technical");
  const expandAll = document.getElementById("expand-all");
  const collapseAll = document.getElementById("collapse-all");
  const pendingStatus = document.getElementById("pending-status");
  const pendingList = document.getElementById("pending-list");
  const languageButtons = [...document.querySelectorAll("[data-language]")];
  let nodes = [];
  let pendingEntries = [];
  let language = "pt";

  const workflowStatuses = {
    "decap-cms/draft": { label: "Rascunho", className: "draft" },
    "decap-cms/pending_review": { label: "Em revisão", className: "review" },
    "decap-cms/pending_publish": { label: "Pronto para publicar", className: "ready" }
  };
  const requiredChecks = ["validate-data", "security", "hugo-build", "links", "content-diff"];
  const readinessStatuses = {
    behind: { label: "Atualizando com o site", className: "checking", detail: "A proposta ficou atrás de uma publicação mais recente. A atualização automática vai sincronizá-la e repetir os testes." },
    checking: { label: "Testes em andamento", className: "checking", detail: "Aguarde os cinco testes terminarem antes de usar Publicar." },
    failed: { label: "Teste com erro", className: "failed", detail: "Abra Rascunhos e revisão para ver qual teste precisa de correção." },
    conflict: { label: "Conflito precisa de ajuda", className: "failed", detail: "Duas alterações atingiram o mesmo conteúdo; um mantenedor técnico precisa conciliá-las." },
    ready: { label: "Pode publicar", className: "publishable", detail: "A proposta está sincronizada e todos os testes obrigatórios passaram." },
    unknown: { label: "Situação sendo consultada", className: "checking", detail: "O GitHub ainda não informou se esta proposta está pronta. Aguarde um pouco e recarregue." }
  };

  const escapeHtml = value => String(value ?? "").replace(/[&<>'"]/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[character]);

  const localizedValue = value => {
    if (!value || typeof value !== "object") return "";
    return value[language] || value.pt || value.en || "";
  };

  const parentLabel = parent => {
    if (parent === "root") return language === "pt" ? "Menu principal" : "Main menu";
    const parentNode = nodes.find(node => node.id === parent);
    return parentNode ? localizedValue(parentNode.rotulo) : parent;
  };

  const renderPending = () => {
    if (!pendingEntries.length) {
      pendingStatus.textContent = "Nenhuma página do mapa está aguardando publicação.";
      pendingList.innerHTML = '<p class="pending-empty">A árvore abaixo representa tudo o que já foi publicado.</p>';
      return;
    }
    pendingStatus.textContent = `${pendingEntries.length} ${pendingEntries.length === 1 ? "página ainda não aparece" : "páginas ainda não aparecem"} na árvore publicada abaixo.`;
    pendingList.innerHTML = pendingEntries.map(entry => {
      const menuLabel = localizedValue(entry.data.rotulo) || entry.id;
      const title = localizedValue(entry.data.pagina && entry.data.pagina.titulo);
      const statusMeta = workflowStatuses[entry.status] || workflowStatuses["decap-cms/draft"];
      const location = entry.partial ? "" : parentLabel(entry.data.parent || "root");
      const detail = entry.partial
        ? "Os detalhes não puderam ser carregados agora; a proposta continua preservada no fluxo."
        : title && title !== menuLabel ? `${title} · Dentro de: ${location}` : `Dentro de: ${location}`;
      const readiness = entry.status === "decap-cms/pending_publish"
        ? (readinessStatuses[entry.readiness] || readinessStatuses.unknown)
        : null;
      const readinessBadge = readiness
        ? `<span class="badge readiness-badge ${readiness.className}">${readiness.label}</span>`
        : "";
      const readinessDetail = readiness ? `<p class="readiness-detail">${escapeHtml(readiness.detail)}</p>` : "";
      return `<article class="pending-card"><div class="badges"><span class="badge workflow-badge ${statusMeta.className}">${statusMeta.label}</span>${readinessBadge}<span class="badge origin-markdown">📝 Ainda não publicada</span></div><h3>${escapeHtml(menuLabel)}</h3><p>${escapeHtml(detail)}</p>${readinessDetail}<div class="actions"><a class="button primary small" href="./#/workflow">Abrir em Rascunhos e revisão</a></div></article>`;
    }).join("");
  };

  const decodeContent = content => {
    const compact = String(content || "").replace(/\n/g, "");
    const bytes = Uint8Array.from(window.atob(compact), character => character.charCodeAt(0));
    return new TextDecoder().decode(bytes);
  };

  const loadReadiness = async pullRequest => {
    const detailUrl = `https://api.github.com/repos/flavioluiz/iea_site_dev/pulls/${encodeURIComponent(pullRequest.number)}`;
    const checksUrl = `https://api.github.com/repos/flavioluiz/iea_site_dev/commits/${encodeURIComponent(pullRequest.head.sha)}/check-runs?per_page=100`;
    try {
      const [detailResponse, checksResponse] = await Promise.all([
        fetch(detailUrl, { referrerPolicy: "no-referrer" }),
        fetch(checksUrl, { referrerPolicy: "no-referrer", headers: { Accept: "application/vnd.github+json" } })
      ]);
      if (!detailResponse.ok || !checksResponse.ok) throw new Error("GitHub indisponível");
      const [detail, checksPayload] = await Promise.all([detailResponse.json(), checksResponse.json()]);
      if (detail.mergeable_state === "behind") return "behind";
      if (detail.mergeable_state === "dirty") return "conflict";
      const checks = new Map((checksPayload.check_runs || []).map(check => [check.name, check]));
      const required = requiredChecks.map(name => checks.get(name));
      if (required.some(check => check && check.status === "completed" && !["success", "neutral", "skipped"].includes(check.conclusion))) return "failed";
      if (required.some(check => !check || check.status !== "completed")) return "checking";
      return "ready";
    } catch (error) {
      return "unknown";
    }
  };

  const loadPendingEntry = async pullRequest => {
    const branchPrefix = "cms/paginas/";
    const identifier = pullRequest.head.ref.slice(branchPrefix.length);
    const repository = pullRequest.head.repo && pullRequest.head.repo.full_name;
    const sha = pullRequest.head.sha || "";
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(identifier) || !/^[0-9a-f]{40}$/.test(sha)) {
      throw new Error("Identificação de proposta inválida");
    }
    const repositoryParts = String(repository || "").split("/");
    if (repositoryParts.length !== 2 || repositoryParts.some(part => !/^[A-Za-z0-9_.-]+$/.test(part))) {
      throw new Error("Repositório de proposta inválido");
    }
    const contentUrl = `https://api.github.com/repos/${repositoryParts.map(encodeURIComponent).join("/")}/contents/data/paginas/${encodeURIComponent(identifier)}.json?ref=${encodeURIComponent(sha)}`;
    const statusLabel = pullRequest.labels.find(label => workflowStatuses[label.name]);
    const readinessPromise = statusLabel.name === "decap-cms/pending_publish"
      ? loadReadiness(pullRequest)
      : Promise.resolve(null);
    try {
      const response = await fetch(contentUrl, { referrerPolicy: "no-referrer" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      const data = JSON.parse(decodeContent(payload.content));
      return { id: identifier, data, status: statusLabel.name, readiness: await readinessPromise, partial: false };
    } catch (error) {
      return {
        id: identifier,
        data: { rotulo: { pt: identifier, en: identifier }, pagina: {}, parent: "root" },
        status: statusLabel.name,
        readiness: await readinessPromise,
        partial: true
      };
    }
  };

  const loadPending = async () => {
    try {
      const response = await fetch("https://api.github.com/repos/flavioluiz/iea_site_dev/pulls?state=open&per_page=100", { referrerPolicy: "no-referrer" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const pullRequests = await response.json();
      const editorialPages = pullRequests.filter(pullRequest => {
        const branch = pullRequest.head && pullRequest.head.ref || "";
        const labels = Array.isArray(pullRequest.labels) ? pullRequest.labels : [];
        return branch.startsWith("cms/paginas/") && labels.some(label => workflowStatuses[label.name]);
      });
      const results = await Promise.allSettled(editorialPages.map(loadPendingEntry));
      pendingEntries = results.filter(result => result.status === "fulfilled").map(result => result.value);
      renderPending();
      if (results.some(result => result.status === "rejected")) {
        pendingStatus.textContent += " Algumas propostas não puderam ser detalhadas; abra Rascunhos e revisão para ver todas.";
      }
    } catch (error) {
      pendingStatus.textContent = "Não foi possível consultar as pendências agora. Elas continuam disponíveis em Rascunhos e revisão.";
      pendingList.innerHTML = '<p class="pending-empty">A árvore publicada continua disponível abaixo.</p>';
    }
  };

  const localizedUrl = node => {
    if (node.tipo === "pagina_editavel") {
      return node.pagina.publicada && node.pagina.slug
        ? new URL(`../${language}/${node.pagina.slug}/`, window.location.href).href
        : "";
    }
    const target = node.url[language] || "";
    if (/^https?:\/\//.test(target)) return target;
    if (!target || target === "#") return "";
    return new URL(`../${language}/${target.replace(/^\//, "")}`, window.location.href).href;
  };

  const editMenuUrl = node => `./${node.protegido ? "?protected=1" : ""}#/edit/paginas/${encodeURIComponent(node.id)}`;
  const createUrl = (parent, kind, label) => {
    const params = new URLSearchParams({ create_parent: parent, create_kind: kind, create_label: label });
    return `./?${params.toString()}#/collections/paginas/new`;
  };
  const removeUrl = node => {
    const params = new URLSearchParams({ intent: "remove", label: node.rotulo[language] || node.id });
    return `./?${params.toString()}#/edit/paginas/${encodeURIComponent(node.id)}`;
  };
  const adminRoute = route => route ? `./${route}` : "";
  const visibilityLabel = node => {
    if (!node.visivel.pt && !node.visivel.en) return "Fora dos dois menus";
    if (node.visivel.pt && node.visivel.en) return "Visível em PT e EN";
    return node.visivel.pt ? "Visível somente em PT" : "Visível somente em EN";
  };
  const originKey = node => {
    if (node.edicao && node.edicao.origem) return node.edicao.origem;
    if (node.tipo === "grupo") return "menu";
    if (node.tipo === "link_externo") return "externo";
    if (["categoria", "separador"].includes(node.tipo)) return "organizacao";
    if (node.tipo === "pagina_editavel") return "markdown";
    return "desconhecida";
  };
  const contentEditor = node => {
    const configured = node.edicao && node.edicao.editor;
    if (configured) return configured[language] || configured.pt || configured.en || "";
    return node.tipo === "pagina_editavel" ? `#/edit/paginas/${encodeURIComponent(node.id)}` : "";
  };

  const summary = (node, childCount, depth) => {
    const role = roleMeta[node.tipo] || roleMeta.pagina_estrutural;
    const origin = originMeta[originKey(node)] || originMeta.desconhecida;
    const titleTag = depth === 0 ? "h2" : "h3";
    const editorialRole = node.edicao && node.edicao.papel
      ? node.edicao.papel[language] || node.edicao.papel.pt || node.edicao.papel.en
      : "";
    const location = editorialRole || (childCount
      ? `${childCount} ${childCount === 1 ? "item dentro" : "itens dentro"}`
      : role.help);
    const hidden = !node.visivel[language];
    const mainPage = node.edicao && node.edicao.principal
      ? '<span class="badge main-page">Página principal da seção</span>'
      : "";
    return `<div class="node-summary"><span class="node-icon" aria-hidden="true">${role.icon}</span><div class="node-heading"><${titleTag}>${escapeHtml(node.rotulo[language] || "Sem nome")}</${titleTag}><p class="location">${escapeHtml(location)}</p></div><div class="badges">${mainPage}<span class="badge origin-${escapeHtml(originKey(node))}">${origin.icon} ${origin.label}</span><span class="badge role">${role.label}</span>${node.protegido ? '<span class="badge locked">🔒 Protegido</span>' : ""}${hidden ? `<span class="badge hidden">${visibilityLabel(node)}</span>` : ""}</div></div>`;
  };

  const body = (node, childCount) => {
    const origin = originMeta[originKey(node)] || originMeta.desconhecida;
    const editor = contentEditor(node);
    const dataEditor = node.edicao && node.edicao.dados_editor;
    const dataLabel = node.edicao && node.edicao.dados_label
      ? node.edicao.dados_label[language] || node.edicao.dados_label.pt
      : "Editar dados";
    const detail = node.edicao && node.edicao.detalhe
      ? node.edicao.detalhe[language] || node.edicao.detalhe.pt
      : origin.label;
    const view = localizedUrl(node);
    const contentAction = editor
      ? `<a class="button primary small" href="${adminRoute(editor)}">${escapeHtml(origin.action || "Editar conteúdo")}</a>`
      : "";
    const dataAction = dataEditor
      ? `<a class="button small" href="${adminRoute(dataEditor)}">${escapeHtml(dataLabel)}</a>`
      : "";
    const menuAction = node.tipo !== "separador"
      ? `<a class="button small" href="${editMenuUrl(node)}">Ajustar no menu</a>`
      : "";
    const viewAction = view
      ? `<a class="button small" href="${escapeHtml(view)}" target="_blank" rel="noopener noreferrer">Ver página</a>`
      : "";
    const sourceAction = node.edicao && node.edicao.fonte
      ? `<a class="button small" href="./fontes-dados.html#${encodeURIComponent(node.edicao.fonte)}">Dados e atualização</a>`
      : "";
    const label = node.rotulo[language] || node.id;
    const addActions = node.tipo === "grupo"
      ? `<div class="structure-actions"><span>Adicionar dentro desta seção:</span><a class="button small add" href="${createUrl(node.id, "page", label)}">＋ Página</a><a class="button small add" href="${createUrl(node.id, "submenu", label)}">＋ Submenu</a></div>`
      : "";
    const removeAction = !node.protegido && childCount === 0
      ? `<a class="button small danger" href="${removeUrl(node)}">Remover…</a>`
      : "";
    const removeHint = !node.protegido && childCount > 0
      ? '<span class="remove-hint">Para remover esta seção, mova ou remova primeiro os itens dentro dela.</span>'
      : "";
    const technical = `<dl class="technical-details"><div><dt>Código</dt><dd>${escapeHtml(node.id)}</dd></div><div><dt>Dentro de</dt><dd>${escapeHtml(node.parent)}</dd></div><div><dt>Ordem</dt><dd>${escapeHtml(node.ordem)}</dd></div><div><dt>Tipo</dt><dd>${escapeHtml(node.tipo)}</dd></div></dl>`;
    return `<div class="node-body"><p class="detail">${escapeHtml(detail)}</p><div class="node-actions">${contentAction}${dataAction}${menuAction}${viewAction}${sourceAction}${removeAction}</div>${addActions}${removeHint}${technical}</div>`;
  };

  const renderNode = (node, childrenByParent, allChildrenByParent, depth = 0) => {
    if (node.tipo === "separador") return '<div class="separator" aria-label="Separador visual"></div>';
    const children = childrenByParent.get(node.id) || [];
    const allChildren = allChildrenByParent.get(node.id) || [];
    const hiddenClass = node.visivel[language] ? "" : " hidden-node";
    const classes = `node origin-${originKey(node)}${hiddenClass}`;
    const header = summary(node, children.length, depth);
    const contents = `${body(node, allChildren.length)}${children.length ? `<div class="children">${children.map(child => renderNode(child, childrenByParent, allChildrenByParent, depth + 1)).join("")}</div>` : ""}`;
    if (children.length) return `<details class="branch ${classes}" data-node-id="${escapeHtml(node.id)}"><summary>${header}</summary>${contents}</details>`;
    return `<article class="leaf ${classes}" data-node-id="${escapeHtml(node.id)}">${header}${contents}</article>`;
  };

  const render = () => {
    const showHidden = hiddenToggle.checked;
    const visible = node => showHidden || node.visivel[language];
    const ordered = [...nodes].sort((a, b) => a.ordem - b.ordem || a.id.localeCompare(b.id));
    const shown = ordered.filter(visible);
    const childrenByParent = new Map();
    const allChildrenByParent = new Map();
    ordered.forEach(node => {
      if (!allChildrenByParent.has(node.parent)) allChildrenByParent.set(node.parent, []);
      allChildrenByParent.get(node.parent).push(node);
    });
    shown.forEach(node => {
      if (!childrenByParent.has(node.parent)) childrenByParent.set(node.parent, []);
      childrenByParent.get(node.parent).push(node);
    });
    const topLevel = childrenByParent.get("root") || [];
    tree.innerHTML = topLevel.map(node => renderNode(node, childrenByParent, allChildrenByParent)).join("");
    const pageCount = shown.filter(node => !["grupo", "categoria", "separador", "link_externo"].includes(node.tipo)).length;
    status.textContent = `${topLevel.length} itens na barra principal · ${pageCount} páginas ou destinos · idioma ${language === "pt" ? "Português" : "English"}${showHidden ? " · incluindo itens ocultos" : ""}`;
    if (!topLevel.length) tree.innerHTML = '<p class="empty">Nenhum item encontrado para este idioma.</p>';
  };

  languageButtons.forEach(button => button.addEventListener("click", () => {
    language = button.dataset.language;
    languageButtons.forEach(item => item.setAttribute("aria-pressed", String(item === button)));
    render();
    renderPending();
  }));
  hiddenToggle.addEventListener("change", render);
  technicalToggle.addEventListener("change", () => {
    document.body.classList.toggle("show-technical", technicalToggle.checked);
  });
  expandAll.addEventListener("click", () => document.querySelectorAll("#map-tree details").forEach(item => { item.open = true; }));
  collapseAll.addEventListener("click", () => document.querySelectorAll("#map-tree details").forEach(item => { item.open = false; }));

  fetch(new URL("../pt/mapa-site.json", window.location.href), { credentials: "same-origin" })
    .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(payload => {
      nodes = payload.nodes.filter(node => node.tipo !== "raiz");
      render();
      renderPending();
    })
    .catch(error => {
      status.textContent = "Não foi possível carregar o mapa. Recarregue a página; os formulários individuais continuam preservados.";
      tree.innerHTML = `<p class="empty">Falha ao carregar a estrutura (${escapeHtml(error.message)}).</p>`;
    });

  loadPending();

  technicalToggle.checked = new URLSearchParams(window.location.search).get("details") === "1";
  document.body.classList.toggle("show-technical", technicalToggle.checked);
})();
