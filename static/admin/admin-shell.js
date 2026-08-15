(() => {
  const loading = document.getElementById("cms-loading");
  if (!loading) return;

  const revealCms = () => {
    const root = document.getElementById("nc-root");
    if (!root || root.childElementCount === 0) return false;

    loading.hidden = true;
    loading.setAttribute("aria-hidden", "true");
    document.body.classList.add("cms-ready");
    return true;
  };

  if (revealCms()) return;

  const observer = new MutationObserver(() => {
    if (revealCms()) observer.disconnect();
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();
