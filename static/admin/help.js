(() => {
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
  bar.style.cssText = "position:fixed;right:16px;bottom:16px;z-index:99999;display:flex;gap:8px;font:600 14px system-ui";
  bar.innerHTML = '<a href="./paginas-especiais.html" target="_blank" rel="noopener noreferrer" style="border:1px solid #173b73;background:white;color:#173b73;padding:9px 13px;border-radius:8px;box-shadow:0 2px 8px #17203322;font:inherit;text-decoration:none">Páginas especiais</a><button type="button" style="border:0;background:#173b73;color:white;padding:10px 14px;border-radius:8px;cursor:pointer;box-shadow:0 2px 8px #17203333;font:inherit">Entenda o fluxo</button>';
  bar.querySelector("button").addEventListener("click", () => dialog.showModal());
  document.body.appendChild(bar);
})();
