(() => {
  const typeMeta = {
    grupo: { icon: "📁", label: "Seção do menu", help: "Abre as opções abaixo" },
    pagina_editavel: { icon: "📄", label: "Página comum", help: "Texto editável neste formulário" },
    pagina_estrutural: { icon: "🧩", label: "Página automática", help: "Montada por dados ou template" },
    link_externo: { icon: "🔗", label: "Link externo", help: "Leva para outro site" },
    categoria: { icon: "🏷️", label: "Título de categoria", help: "Organiza opções dentro do submenu" },
    separador: { icon: "", label: "Separador", help: "Espaço visual no submenu" },
    raiz: { icon: "", label: "Raiz técnica", help: "" }
  };

  const tree = document.getElementById("map-tree");
  const status = document.getElementById("map-status");
  const hiddenToggle = document.getElementById("show-hidden");
  const languageButtons = [...document.querySelectorAll("[data-language]")];
  let nodes = [];
  let language = "pt";

  const escapeHtml = value => String(value ?? "").replace(/[&<>'"]/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[character]);

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

  const editUrl = node => `./#/edit/paginas/${encodeURIComponent(node.id)}`;
  const visibilityLabel = node => {
    if (!node.visivel.pt && !node.visivel.en) return "Fora dos dois menus";
    if (node.visivel.pt && node.visivel.en) return "Visível em PT e EN";
    return node.visivel.pt ? "Visível somente em PT" : "Visível somente em EN";
  };

  const nodeContent = (node, child = false) => {
    const meta = typeMeta[node.tipo] || typeMeta.pagina_estrutural;
    const view = localizedUrl(node);
    const hidden = !node.visivel[language];
    const heading = child ? "h3" : "h2";
    return `<div class="node-title-row"><span class="icon" aria-hidden="true">${meta.icon}</span><div class="node-title"><${heading}>${escapeHtml(node.rotulo[language] || "Sem nome")}</${heading}><p class="kind">${meta.help}</p></div></div>
      <div class="badges"><span class="badge type-badge">${meta.label}</span>${node.protegido ? '<span class="badge locked">🔒 Não excluir</span>' : ""}${hidden ? `<span class="badge hidden">${visibilityLabel(node)}</span>` : ""}</div>
      <div class="node-actions"><a class="button small" href="${editUrl(node)}">Editar</a>${view ? `<a class="button small" href="${escapeHtml(view)}" target="_blank" rel="noopener noreferrer">Ver página</a>` : ""}</div>`;
  };

  const renderChild = node => {
    if (node.tipo === "separador") return '<div class="child type-separador" aria-label="Separador visual"></div>';
    const hiddenClass = node.visivel[language] ? "" : " hidden-node";
    return `<article class="child type-${node.tipo}${hiddenClass}" title="Identificador técnico: ${escapeHtml(node.id)}">${nodeContent(node, true)}</article>`;
  };

  const render = () => {
    const showHidden = hiddenToggle.checked;
    const visible = node => showHidden || node.visivel[language];
    const ordered = [...nodes].sort((a, b) => a.ordem - b.ordem || a.id.localeCompare(b.id));
    const topLevel = ordered.filter(node => node.parent === "root" && visible(node));

    tree.innerHTML = topLevel.map(node => {
      const children = ordered.filter(child => child.parent === node.id && visible(child));
      const hiddenClass = node.visivel[language] ? "" : " hidden-node";
      return `<article class="branch type-${node.tipo}${children.length ? " has-children" : ""}${hiddenClass}" title="Identificador técnico: ${escapeHtml(node.id)}"><div class="node-main">${nodeContent(node)}</div>${children.length ? `<div class="children">${children.map(renderChild).join("")}</div>` : ""}</article>`;
    }).join("");

    status.textContent = `${topLevel.length} itens na barra principal · idioma ${language === "pt" ? "Português" : "English"}${showHidden ? " · incluindo itens ocultos" : ""}`;
    if (!topLevel.length) tree.innerHTML = '<p class="empty">Nenhum item encontrado para este idioma.</p>';
  };

  languageButtons.forEach(button => button.addEventListener("click", () => {
    language = button.dataset.language;
    languageButtons.forEach(item => item.setAttribute("aria-pressed", String(item === button)));
    render();
  }));
  hiddenToggle.addEventListener("change", render);

  fetch(new URL("../pt/mapa-site.json", window.location.href), { credentials: "same-origin" })
    .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(payload => {
      nodes = payload.nodes.filter(node => node.tipo !== "raiz");
      render();
    })
    .catch(error => {
      status.textContent = "Não foi possível carregar o mapa. Recarregue a página ou use a Lista avançada.";
      tree.innerHTML = `<p class="empty">Falha ao carregar a estrutura (${escapeHtml(error.message)}).</p>`;
    });
})();
