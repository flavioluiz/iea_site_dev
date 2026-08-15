(() => {
  const status = document.getElementById("sources-status");
  const states = {
    migrated: "Carga inicial migrada; automação ainda não confirmou um novo ciclo",
    complete: "Última execução concluída",
    completed: "Última execução concluída",
    success: "Última execução concluída"
  };
  const thresholds = { scopus: 45, biblioteca: 14 };

  const formatDate = value => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Data não registrada";
    return new Intl.DateTimeFormat("pt-BR", {
      dateStyle: "long", timeZone: "UTC"
    }).format(date);
  };

  const age = (value, source) => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return { label: "Sem data", className: "old" };
    const days = Math.max(0, Math.floor((Date.now() - date.getTime()) / 86400000));
    const threshold = thresholds[source];
    return {
      label: days === 0 ? "Atualizado hoje" : `${days} ${days === 1 ? "dia" : "dias"} desde a carga`,
      className: days > threshold * 2 ? "old" : days > threshold ? "warn" : ""
    };
  };

  const setText = (card, field, value) => {
    const target = card.querySelector(`[data-field="${field}"]`);
    if (target) target.textContent = value;
  };

  fetch(new URL("../pt/fontes-dados.json", window.location.href), { credentials: "same-origin" })
    .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(payload => {
      payload.sources.forEach(source => {
        const card = document.querySelector(`[data-source="${source.id}"]`);
        if (!card) return;
        const manifest = source.manifest || {};
        const lastRun = manifest.last_complete_run || manifest.generated_at;
        const freshness = age(lastRun, source.id);
        setText(card, "date", formatDate(lastRun));
        setText(card, "records", Number.isFinite(manifest.records) ? manifest.records.toLocaleString("pt-BR") : "Não informado");
        setText(card, "state", states[manifest.status] || manifest.status || "Não informado");
        setText(card, "freshness", freshness.label);
        const freshnessNode = card.querySelector('[data-field="freshness"]');
        freshnessNode.className = `freshness ${freshness.className}`.trim();
        if (source.id === "biblioteca" && manifest.counts) {
          const counts = card.querySelector('[data-field="counts"]');
          const theses = manifest.counts.teses_dissertacoes_iea;
          const tgs = manifest.counts.trabalhos_graduacao_iea;
          counts.textContent = `Recorte IEA: ${Number(theses).toLocaleString("pt-BR")} dissertações/teses e ${Number(tgs).toLocaleString("pt-BR")} TGS.`;
        }
      });
      status.textContent = "Datas e contagens carregadas diretamente dos bancos publicados.";
    })
    .catch(error => {
      status.textContent = `Não foi possível ler os manifests (${error.message}). A última versão publicada dos bancos continua preservada.`;
    });
})();
