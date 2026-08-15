(() => {
  const redirectTechnicalMenuList = () => {
    if (/^#\/collections\/paginas\/?$/.test(window.location.hash)) {
      window.location.replace("./mapa-visual.html");
      return true;
    }
    return false;
  };
  if (redirectTechnicalMenuList()) return;
  window.addEventListener("hashchange", redirectTechnicalMenuList);

  const params = new URLSearchParams(window.location.search);
  const createParent = params.get("create_parent") || "";
  const createKind = params.get("create_kind") || "";
  const createLabel = params.get("create_label") || createParent;
  const validCreateContext = /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(createParent)
    && ["page", "submenu"].includes(createKind);

  if (validCreateContext && window.CMS && typeof window.CMS.registerEventListener === "function") {
    window.CMS.registerEventListener({
      name: "preSave",
      handler: ({ entry }) => {
        const data = entry.get("data");
        if (!/^#\/collections\/paginas\/new\/?$/.test(window.location.hash)) return data;
        const portugueseLabel = data.getIn(["rotulo", "pt"]) || "";
        const englishLabel = data.getIn(["rotulo", "en"]) || portugueseLabel;
        let prepared = data
          .set("protegido", false)
          .set("parent", createParent)
          .set("tipo", createKind === "submenu" ? "grupo" : "pagina_editavel")
          .set("ordem", data.get("ordem") ?? 100)
          .setIn(["visivel", "pt"], data.getIn(["visivel", "pt"]) ?? true)
          .setIn(["visivel", "en"], data.getIn(["visivel", "en"]) ?? true)
          .setIn(["rotulo", "pt"], portugueseLabel)
          .setIn(["rotulo", "en"], englishLabel)
          .setIn(["pagina", "descricao", "pt"], data.getIn(["pagina", "descricao", "pt"]) || "")
          .setIn(["pagina", "descricao", "en"], data.getIn(["pagina", "descricao", "en"]) || "")
          .setIn(["pagina", "conteudo", "pt"], data.getIn(["pagina", "conteudo", "pt"]) || "")
          .setIn(["pagina", "conteudo", "en"], data.getIn(["pagina", "conteudo", "en"]) || "");
        if (createKind === "submenu") {
          prepared = prepared
            .setIn(["url", "pt"], "#")
            .setIn(["url", "en"], "#")
            .setIn(["pagina", "slug"], "")
            .setIn(["pagina", "publicada"], false)
            .setIn(["pagina", "titulo", "pt"], "")
            .setIn(["pagina", "titulo", "en"], "");
        } else {
          const identifier = data.get("id") || "";
          prepared = prepared
            .setIn(["url", "pt"], "")
            .setIn(["url", "en"], "")
            .setIn(["pagina", "slug"], data.getIn(["pagina", "slug"]) || identifier)
            .setIn(["pagina", "publicada"], data.getIn(["pagina", "publicada"]) ?? true)
            .setIn(["pagina", "titulo", "pt"], data.getIn(["pagina", "titulo", "pt"]) || portugueseLabel)
            .setIn(["pagina", "titulo", "en"], data.getIn(["pagina", "titulo", "en"]) || englishLabel);
        }
        return prepared;
      }
    });
  }

  const contextualNotice = document.createElement("aside");
  contextualNotice.setAttribute("role", "status");
  contextualNotice.style.cssText = "display:none;position:fixed;left:16px;bottom:16px;z-index:99998;max-width:430px;padding:13px 15px;border:1px solid #b8c7da;border-left:5px solid #176b46;border-radius:10px;background:white;box-shadow:0 4px 18px #1720332b;color:#172033;font:14px/1.45 system-ui";
  document.body.appendChild(contextualNotice);

  const showContextualNotice = () => {
    contextualNotice.replaceChildren();
    contextualNotice.style.display = "none";
    contextualNotice.style.borderLeftColor = "#176b46";

    if (validCreateContext && /^#\/collections\/paginas\/new\/?$/.test(window.location.hash)) {
      const strong = document.createElement("strong");
      strong.textContent = createKind === "submenu" ? "Novo submenu" : "Nova página";
      contextualNotice.append(strong, document.createElement("br"));
      contextualNotice.append(`Será criado dentro de “${createLabel}”. O mapa aplicará automaticamente esse local e o tipo correto quando você salvar.`);
      contextualNotice.style.display = "block";
      return;
    }

    if (params.get("intent") === "remove" && /^#\/edit\/paginas\//.test(window.location.hash)) {
      const strong = document.createElement("strong");
      strong.textContent = `Remover “${params.get("label") || "este item"}”`;
      contextualNotice.append(strong, document.createElement("br"));
      contextualNotice.append("Confira se escolheu o item correto e use Excluir nesta ficha. Itens protegidos devem ser ocultados, não apagados.");
      contextualNotice.style.borderLeftColor = "#b42318";
      contextualNotice.style.display = "block";
      return;
    }

    if (params.get("protected") === "1" && /^#\/edit\/paginas\//.test(window.location.hash)) {
      const strong = document.createElement("strong");
      strong.textContent = "Item estrutural protegido";
      contextualNotice.append(strong, document.createElement("br"));
      contextualNotice.append("Você pode renomear, mover ou ocultar este item. Não use Excluir: ele corresponde a uma parte necessária do site.");
      contextualNotice.style.display = "block";
      return;
    }

    const collectionMatch = window.location.hash.match(/^#\/collections\/(pessoal|laboratorios)\/?$/);
    if (collectionMatch) {
      const isPeople = collectionMatch[1] === "pessoal";
      const strong = document.createElement("strong");
      strong.textContent = isPeople ? "Editar ou retirar uma pessoa" : "Editar ou excluir um laboratório";
      contextualNotice.append(strong, document.createElement("br"));
      contextualNotice.append(isPeople
        ? "Abra a ficha desejada. Prefira desativar quem saiu; para apagar definitivamente, use Excluir dentro da ficha."
        : "Abra a ficha desejada e use Excluir dentro dela. O restante da lista não será alterado.");
      contextualNotice.style.display = "block";
    }
  };
  showContextualNotice();
  window.addEventListener("hashchange", showContextualNotice);

  const dialog = document.createElement("dialog");
  dialog.setAttribute("aria-labelledby", "workflow-help-title");
  dialog.style.cssText = "max-width:680px;width:calc(100% - 32px);border:0;border-radius:14px;padding:0;box-shadow:0 18px 60px #17203355;color:#172033;font:16px/1.5 system-ui";
  dialog.innerHTML = `
    <div style="padding:24px">
      <div style="display:flex;align-items:start;justify-content:space-between;gap:16px">
        <div>
          <h2 id="workflow-help-title" style="margin:0;color:#173b73;font-size:24px">O que cada ação faz?</h2>
          <p style="margin:6px 0 18px;color:#526078">Os estados organizam o trabalho. Só <strong>Publicar</strong> altera o site no ar.</p>
        </div>
        <button type="button" data-close-dialog aria-label="Fechar" style="border:0;background:#eef2f7;border-radius:999px;width:34px;height:34px;font-size:20px;cursor:pointer">×</button>
      </div>
      <dl style="display:grid;grid-template-columns:max-content 1fr;gap:10px 16px;margin:0">
        <dt><strong>Salvar</strong></dt><dd style="margin:0">Guarda a alteração na proposta; não publica.</dd>
        <dt><strong>Rascunho</strong></dt><dd style="margin:0">Ainda está sendo preparado.</dd>
        <dt><strong>Em revisão</strong></dt><dd style="margin:0">Está pronto para outra pessoa conferir.</dd>
        <dt><strong>Pronto</strong></dt><dd style="margin:0">A revisão terminou; ainda não está no ar.</dd>
        <dt><strong>Ver prévia</strong></dt><dd style="margin:0">Abre o site de teste; não muda o estado.</dd>
        <dt><strong>Publicar</strong></dt><dd style="margin:0">Disponível a mantenedores. Mescla a proposta e inicia a atualização do site.</dd>
      </dl>
      <div style="margin-top:18px;padding:12px 14px;background:#fff7df;border-left:4px solid #d69b16;border-radius:6px">
        Se <strong>Publicar</strong> der erro, aguarde os testes e a prévia terminarem e tente novamente. Trocar entre Rascunho e Pronto não corrige a proposta.
      </div>
      <p style="margin:18px 0 0"><strong>Editor externo:</strong> usa Rascunho e Em revisão; um mantenedor publica. <strong>Mantenedor:</strong> também vê Pronto e Publicar.</p>
      <p style="margin:14px 0 0"><a href="./guia.html" target="_blank" rel="noopener noreferrer" style="color:#173b73;font-weight:700">Abrir o guia completo</a></p>
    </div>`;
  dialog.addEventListener("click", event => {
    if (event.target === dialog || event.target.closest("[data-close-dialog]")) dialog.close();
  });
  document.body.appendChild(dialog);

  const bar = document.createElement("nav");
  bar.setAttribute("aria-label", "Ajuda do editor");
  bar.style.cssText = "position:fixed;right:16px;bottom:16px;z-index:99999;display:flex;justify-content:flex-end;flex-wrap:wrap;gap:8px;max-width:calc(100% - 32px);font:600 14px system-ui";
  bar.innerHTML = '<a href="./mapa-visual.html" style="border:0;background:#176b46;color:white;padding:10px 14px;border-radius:8px;box-shadow:0 2px 8px #17203333;font:inherit;text-decoration:none">Mapa do site</a><a href="./fontes-dados.html" style="border:1px solid #173b73;background:white;color:#173b73;padding:9px 13px;border-radius:8px;box-shadow:0 2px 8px #17203322;font:inherit;text-decoration:none">Fontes de dados</a><a href="./paginas-especiais.html" target="_blank" rel="noopener noreferrer" style="border:1px solid #173b73;background:white;color:#173b73;padding:9px 13px;border-radius:8px;box-shadow:0 2px 8px #17203322;font:inherit;text-decoration:none">Como as páginas são montadas</a><button type="button" style="border:0;background:#173b73;color:white;padding:10px 14px;border-radius:8px;cursor:pointer;box-shadow:0 2px 8px #17203333;font:inherit">Entenda o fluxo</button>';
  bar.querySelector("button").addEventListener("click", () => dialog.showModal());
  document.body.appendChild(bar);
  const placeContextualNotice = () => {
    contextualNotice.style.bottom = `${Math.ceil(bar.getBoundingClientRect().height) + 28}px`;
  };
  window.requestAnimationFrame(placeContextualNotice);
  window.addEventListener("resize", placeContextualNotice);
})();
