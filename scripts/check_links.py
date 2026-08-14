#!/usr/bin/env python3
"""Check generated HTML links and assets, including a GitHub Pages subpath."""

from __future__ import annotations

import argparse
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse


class References(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.values: list[tuple[str, str]] = []
        self.unsafe_blank_links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "a" and (attributes.get("target") or "").casefold() == "_blank":
            rel = {item.casefold() for item in (attributes.get("rel") or "").split()}
            if not {"noopener", "noreferrer"}.issubset(rel):
                self.unsafe_blank_links.append(attributes.get("href") or "<sem href>")
        for name in ("href", "src"):
            value = attributes.get(name)
            if value:
                self.values.append((name, value))


def target_path(public: Path, route: str) -> Path | None:
    relative = unquote(route).lstrip("/")
    candidate = public / relative
    if route.endswith("/"):
        return candidate / "index.html"
    if candidate.is_file():
        return candidate
    if not Path(relative).suffix:
        return candidate / "index.html"
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public", type=Path, default=Path("public"))
    parser.add_argument("--base-url", default="https://flavioluiz.github.io/iea_site/")
    args = parser.parse_args()

    public = args.public.resolve()
    base = urlparse(args.base_url)
    base_path = base.path.rstrip("/")
    problems: list[str] = []
    checked: set[tuple[Path, str]] = set()

    for html_path in sorted(public.rglob("*.html")):
        parser_instance = References()
        parser_instance.feed(html_path.read_text(encoding="utf-8", errors="replace"))
        for raw in parser_instance.unsafe_blank_links:
            problems.append(
                f"{html_path.relative_to(public)}: link target=_blank sem rel=\"noopener noreferrer\" ({raw!r})"
            )
        for attribute, raw in parser_instance.values:
            parsed = urlparse(raw)
            if parsed.scheme in {"data", "mailto", "tel", "javascript"}:
                continue
            if parsed.scheme and parsed.scheme not in {"http", "https"}:
                continue
            if parsed.netloc and parsed.netloc != base.netloc:
                continue

            if parsed.netloc:
                if base_path and parsed.path != base_path and not parsed.path.startswith(base_path + "/"):
                    # A different site hosted under the same account/domain.
                    continue
                path = parsed.path
            elif raw.startswith("/"):
                path = parsed.path
            else:
                relative_parent = str(html_path.parent.relative_to(public)).strip(".")
                current_route = base_path + "/" + relative_parent
                path = urlparse(current_route.rstrip("/") + "/" + parsed.path).path

            if base_path and path != base_path and not path.startswith(base_path + "/"):
                problems.append(
                    f"{html_path.relative_to(public)}: {attribute}={raw!r} ignora o prefixo {base_path}/"
                )
                continue
            route = path[len(base_path):] if base_path else path
            route = route or "/"
            key = (html_path, raw)
            if key in checked:
                continue
            checked.add(key)
            target = target_path(public, route)
            if target is not None and not target.exists():
                problems.append(
                    f"{html_path.relative_to(public)}: {attribute}={raw!r} aponta para arquivo inexistente"
                )

    if problems:
        print("Link check failed:", file=sys.stderr)
        for problem in problems[:200]:
            print(f"- {problem}", file=sys.stderr)
        if len(problems) > 200:
            print(f"- ... e mais {len(problems) - 200} problemas", file=sys.stderr)
        return 1
    print(f"Link check passed ({len(checked)} referências internas).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
