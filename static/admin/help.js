(() => {
  const bar = document.createElement("nav");
  bar.setAttribute("aria-label", "Ajuda do editor");
  bar.style.cssText = "position:fixed;right:16px;bottom:16px;z-index:99999;display:flex;gap:8px;font:600 14px system-ui";
  bar.innerHTML = [
    '<a href="./guia.html" target="_blank" rel="noopener noreferrer" style="background:#173b73;color:white;padding:10px 14px;border-radius:8px;text-decoration:none">Guia passo a passo</a>',
    '<a href="https://github.com/flavioluiz/iea_site_dev/edit/main/data/pessoal/professores.json" target="_blank" rel="noopener noreferrer" style="background:white;color:#173b73;padding:10px 14px;border:1px solid #173b73;border-radius:8px;text-decoration:none">Editar JSON completo</a>'
  ].join("");
  document.body.appendChild(bar);
})();
