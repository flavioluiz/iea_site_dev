(() => {
  const bar = document.createElement("nav");
  bar.setAttribute("aria-label", "Ajuda do editor");
  bar.style.cssText = "position:fixed;right:16px;bottom:16px;z-index:99999;display:flex;gap:8px;font:600 14px system-ui";
  bar.innerHTML = '<a href="./guia.html" target="_blank" rel="noopener noreferrer" style="background:#173b73;color:white;padding:10px 14px;border-radius:8px;text-decoration:none;box-shadow:0 2px 8px #17203333">Ajuda</a>';
  document.body.appendChild(bar);
})();
