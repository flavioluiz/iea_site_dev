#!/usr/bin/env python3
"""Fail on committed secrets, unsafe Markdown, or disguised editorial uploads."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".html", ".js", ".json", ".md", ".py", ".sh", ".toml", ".yaml", ".yml"}
SKIP_PARTS = {".git", "node_modules", "public", "resources", "__pycache__"}
MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
SAFE_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}

SECRET_PATTERNS = {
    "chave privada": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "token GitHub": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    "access key AWS": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "segredo atribuído literalmente": re.compile(
        r"(?i)\b(?:api[_-]?key|client[_-]?secret|access[_-]?token|auth[_-]?token)"
        r"\s*[:=]\s*['\"][A-Za-z0-9_./+=-]{16,}['\"]"
    ),
}

DANGEROUS_MARKDOWN = {
    "tag script": re.compile(r"<\s*script\b", re.IGNORECASE),
    "handler HTML": re.compile(r"\bon[a-z]+\s*=", re.IGNORECASE),
    "protocolo javascript": re.compile(r"javascript\s*:", re.IGNORECASE),
    "HTML incorporado": re.compile(r"<\s*(?:iframe|object|embed)\b", re.IGNORECASE),
    "data URL HTML": re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
}


def report(problems: list[str], path: Path, label: str, line: int | None = None) -> None:
    location = str(path.relative_to(ROOT))
    if line is not None:
        location += f":{line}"
    problems.append(f"{location}: {label}")


def scan_text(problems: list[str]) -> None:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_PARTS for part in path.relative_to(ROOT).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            report(problems, path, "arquivo textual não é UTF-8")
            continue
        for label, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(text):
                report(problems, path, f"possível {label}", text.count("\n", 0, match.start()) + 1)


def scan_editorial_content(problems: list[str]) -> None:
    paths = list((ROOT / "content").rglob("*.md"))
    # JSON edited in the CMS and metadata collected from external sources can
    # also reach browser-side renderers. Treat it as untrusted content too.
    paths.extend((ROOT / "data").rglob("*.json"))
    for path in sorted(paths):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            report(problems, path, "conteúdo editorial não é UTF-8")
            continue
        for label, pattern in DANGEROUS_MARKDOWN.items():
            for match in pattern.finditer(text):
                report(problems, path, f"conteúdo proibido: {label}", text.count("\n", 0, match.start()) + 1)


def scan_images(problems: list[str]) -> None:
    for folder_name in ("pessoal", "laboratorios"):
        folder = ROOT / "static" / "images" / folder_name
        if not folder.exists():
            continue
        for path in sorted(folder.iterdir()):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                report(problems, path, "extensão de foto não permitida")
                continue
            if path.stat().st_size > MAX_IMAGE_BYTES:
                report(problems, path, "foto excede 2 MB")
            if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", path.name):
                report(problems, path, "nome da foto deve usar somente minúsculas ASCII, números, ponto, _ e -")
            try:
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    if image.format not in SAFE_IMAGE_FORMATS:
                        report(problems, path, "conteúdo real da foto não é JPEG, PNG ou WebP")
                    width, height = image.size
                    if min(width, height) < 80 or max(width, height) > 4096:
                        report(problems, path, f"dimensões fora do intervalo 80–4096 px ({width}x{height})")
            except (UnidentifiedImageError, OSError) as exc:
                report(problems, path, f"foto inválida ({exc})")


def scan_documents(problems: list[str]) -> None:
    folder = ROOT / "static" / "documents"
    for path in sorted(folder.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() != ".pdf":
            report(problems, path, "somente PDF é permitido em static/documents")
        if path.stat().st_size > MAX_DOCUMENT_BYTES:
            report(problems, path, "documento excede 10 MB")
        try:
            if path.read_bytes()[:5] != b"%PDF-":
                report(problems, path, "arquivo disfarçado: assinatura PDF ausente")
        except OSError as exc:
            report(problems, path, f"documento ilegível ({exc})")


def main() -> int:
    problems: list[str] = []
    scan_text(problems)
    scan_editorial_content(problems)
    scan_images(problems)
    scan_documents(problems)
    if problems:
        print("Security check failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    print("Security check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
