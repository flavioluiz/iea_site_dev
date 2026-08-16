from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class AdminCspTests(unittest.TestCase):
    def test_csp_supports_decap_without_opening_inline_scripts(self) -> None:
        index = (ROOT / "static/admin/index.html").read_text(encoding="utf-8")
        csp = index.split('http-equiv="Content-Security-Policy" content="', 1)[1].split('"', 1)[0]

        self.assertIn("script-src 'self' 'unsafe-eval' https://unpkg.com", csp)
        self.assertNotIn("script-src 'self' 'unsafe-inline'", csp)
        self.assertIn("style-src 'unsafe-inline' https://fonts.googleapis.com", csp)
        self.assertIn("font-src data: https://fonts.gstatic.com", csp)
        self.assertIn("connect-src 'self' https://api.github.com https://github.com https://unpkg.com", csp)
        self.assertNotIn("frame-ancestors", csp)

    def test_frame_guard_runs_before_decap(self) -> None:
        index = (ROOT / "static/admin/index.html").read_text(encoding="utf-8")
        guard_position = index.index('src="./frame-guard.js"')
        decap_position = index.index("decap-cms@3.15.1/dist/decap-cms.js")
        guard = (ROOT / "static/admin/frame-guard.js").read_text(encoding="utf-8")

        self.assertLess(guard_position, decap_position)
        self.assertIn("window.self !== window.top", guard)
        self.assertIn("window.stop()", guard)

    def test_intro_is_removed_when_decap_is_ready(self) -> None:
        index = (ROOT / "static/admin/index.html").read_text(encoding="utf-8")
        shell = (ROOT / "static/admin/admin-shell.js").read_text(encoding="utf-8")

        self.assertIn('id="cms-loading"', index)
        self.assertIn('src="./admin-shell.js"', index)
        self.assertIn('getElementById("nc-root")', shell)
        self.assertIn("loading.hidden = true", shell)
        self.assertIn('classList.add("cms-ready")', shell)

    def test_admin_does_not_offer_raw_json_editing(self) -> None:
        help_script = (ROOT / "static/admin/help.js").read_text(encoding="utf-8")
        self.assertNotIn("Editar JSON completo", help_script)
        self.assertNotIn("/edit/main/data/", help_script)

    def test_admin_explains_statuses_and_account_roles(self) -> None:
        help_script = (ROOT / "static/admin/help.js").read_text(encoding="utf-8")
        index = (ROOT / "static/admin/index.html").read_text(encoding="utf-8")
        publication_status = (ROOT / "static/admin/publication-status.js").read_text(encoding="utf-8")
        self.assertIn("Entenda o fluxo", help_script)
        self.assertIn("Editor externo", help_script)
        self.assertIn("Mantenedor", help_script)
        self.assertIn("Só <strong>Publicar</strong> altera o site no ar", help_script)
        self.assertIn('src="./publication-status.js', index)
        self.assertIn('name: "prePublish"', publication_status)
        self.assertIn('name: "postPublish"', publication_status)
        self.assertIn("Alteração aceita — preparando o site", publication_status)
        self.assertIn("Publicação em andamento", publication_status)
        self.assertIn("Publicação concluída", publication_status)
        self.assertIn("actions/workflows/deploy.yml/runs", publication_status)
        self.assertIn("window.localStorage", publication_status)

    def test_admin_logo_uses_the_current_site_origin(self) -> None:
        config = (ROOT / "static/admin/config.yml").read_text(encoding="utf-8")
        self.assertIn("logo_url: ../images/ita_logo.png", config)
        self.assertNotIn("logo_url: https://", config)

    def test_special_pages_guide_has_no_script_and_is_linked_from_admin(self) -> None:
        guide = (ROOT / "static/admin/paginas-especiais.html").read_text(encoding="utf-8")
        help_script = (ROOT / "static/admin/help.js").read_text(encoding="utf-8")

        self.assertIn("Como as páginas são montadas", guide)
        self.assertIn('href="./mapa-visual.html">← Voltar ao mapa do site', guide)
        self.assertIn("Markdown completo", guide)
        self.assertIn("Solicitar alteração maior", guide)
        self.assertNotIn("<script", guide)
        self.assertIn("./paginas-especiais.html", help_script)

    def test_visual_site_map_is_safe_and_linked_from_admin(self) -> None:
        page = (ROOT / "static/admin/mapa-visual.html").read_text(encoding="utf-8")
        script = (ROOT / "static/admin/mapa-visual.js").read_text(encoding="utf-8")
        help_script = (ROOT / "static/admin/help.js").read_text(encoding="utf-8")

        self.assertIn("Mapa visual do site", page)
        self.assertIn("script-src 'self'", page)
        self.assertNotIn("unsafe-eval", page)
        self.assertIn("../pt/mapa-site.json", script)
        self.assertIn("connect-src 'self' https://api.github.com", page)
        self.assertIn("pending-panel", page)
        self.assertIn('href="./#/collections/paginas_estruturais">Editar textos e cadastros', page)
        self.assertNotIn("Voltar ao editor", page)
        self.assertIn("https://api.github.com/repos/flavioluiz/iea_site_dev/pulls", script)
        self.assertIn("decap-cms/pending_publish", script)
        self.assertIn("check-runs?per_page=100", script)
        self.assertIn("Pode publicar", script)
        self.assertIn("Atualizando com o site", script)
        self.assertIn("#/workflow", page)
        self.assertIn("Rascunhos e revisão", help_script)
        self.assertIn("Abrir tudo", page)
        self.assertIn("Markdown completo", page)
        self.assertIn("originMeta", script)
        self.assertIn("Ajustar no menu", script)
        self.assertIn("./mapa-visual.html", help_script)
        self.assertIn("./publication-status.js", page)

    def test_technical_page_list_redirects_to_visual_map(self) -> None:
        help_script = (ROOT / "static/admin/help.js").read_text(encoding="utf-8")
        self.assertIn("redirectTechnicalMenuList", help_script)
        self.assertNotIn("advancedMenuView", help_script)
        self.assertNotIn("advanced=1", help_script)
        self.assertIn("./mapa-visual.html", help_script)

    def test_visual_tree_has_contextual_create_and_remove_actions(self) -> None:
        page = (ROOT / "static/admin/mapa-visual.html").read_text(encoding="utf-8")
        map_script = (ROOT / "static/admin/mapa-visual.js").read_text(encoding="utf-8")
        help_script = (ROOT / "static/admin/help.js").read_text(encoding="utf-8")

        self.assertIn("create_parent=root", page)
        self.assertIn("create_kind=submenu", page)
        self.assertIn("Adicionar dentro desta seção", map_script)
        self.assertIn("Remover…", map_script)
        self.assertIn('name: "preSave"', help_script)
        self.assertIn('.set("parent", createParent)', help_script)
        self.assertIn('.set("tipo", createKind', help_script)

    def test_data_sources_dashboard_reads_generated_manifests(self) -> None:
        page = (ROOT / "static/admin/fontes-dados.html").read_text(encoding="utf-8")
        script = (ROOT / "static/admin/fontes-dados.js").read_text(encoding="utf-8")
        output = (ROOT / "layouts/index.fontesdados.json").read_text(encoding="utf-8")
        config = (ROOT / "config/_default/config.yaml").read_text(encoding="utf-8")

        self.assertIn("Fontes de dados e atualizações", page)
        self.assertIn("../pt/fontes-dados.json", script)
        self.assertIn("last_complete_run", script)
        self.assertIn(".Site.Data.generated.scopus.manifest", output)
        self.assertIn(".Site.Data.generated.biblioteca.manifest", output)
        self.assertIn("FONTESDADOS", config)
        self.assertIn("connect-src 'self' https://api.github.com", page)
        self.assertIn("Somente testar", page)
        self.assertIn("actions/workflows/update-library.yml/runs", script)
        self.assertIn("Nada foi enviado ao site", script)
        self.assertIn("GitHub bloqueou a abertura da proposta", script)


if __name__ == "__main__":
    unittest.main()
