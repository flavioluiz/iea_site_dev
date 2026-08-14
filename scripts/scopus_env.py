"""Shared, secret-safe pybliometrics initialization."""

from __future__ import annotations

import os



def read_scopus_credentials() -> tuple[str, str | None]:
    """Return credentials from the process environment without logging them."""
    api_key = os.environ.get("SCOPUS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "SCOPUS_API_KEY is required. Store it in the private automation "
            "repository or runner environment; never add it to Git."
        )
    return api_key, os.environ.get("SCOPUS_INST_TOKEN") or None


def scopus_headers() -> dict[str, str]:
    api_key, institution_token = read_scopus_credentials()
    headers = {"X-ELS-APIKey": api_key, "Accept": "application/json"}
    if institution_token:
        headers["X-ELS-Insttoken"] = institution_token
    return headers


def configure_pybliometrics() -> None:
    import pybliometrics

    api_key, institution_token = read_scopus_credentials()
    pybliometrics.init(keys=[api_key], inst_tokens=[institution_token])
