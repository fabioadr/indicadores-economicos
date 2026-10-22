"""OAuth2 JWT grant da service account via httpx (sem google-api-python-client)."""

from __future__ import annotations

import time
from pathlib import Path

import httpx
from google.auth import jwt
from google.oauth2 import service_account

from pipeline.gsc.exceptions import GscAuthError, GscConfigError

SCOPES = ("https://www.googleapis.com/auth/webmasters.readonly",)
TOKEN_URI = "https://oauth2.googleapis.com/token"
_TOKEN_LIFETIME_SECS = 3600


def fetch_access_token(
    credentials_path: Path,
    *,
    http: httpx.Client | None = None,
) -> str:
    """Troca o JWT da service account por um access token."""
    if not credentials_path.exists():
        raise GscConfigError(
            f"GSC_CREDENTIALS_PATH não encontrado: {credentials_path}. "
            "Ver docs/gsc/SETUP.md."
        )
    try:
        creds = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=list(SCOPES),
        )
    except (OSError, ValueError) as exc:
        raise GscAuthError(f"JSON da service account inválido: {exc}") from exc

    now = int(time.time())
    payload = {
        "aud": TOKEN_URI,
        "exp": now + _TOKEN_LIFETIME_SECS,
        "iat": now,
        "iss": creds.service_account_email,
        "scope": " ".join(SCOPES),
    }
    assertion = jwt.encode(creds.signer, payload)
    if isinstance(assertion, bytes):
        assertion = assertion.decode("utf-8")

    close = http is None
    client = http or httpx.Client(timeout=30)
    try:
        response = client.post(
            TOKEN_URI,
            data={
                "assertion": assertion,
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            },
        )
        if response.status_code >= 400:
            raise GscAuthError(
                f"Token endpoint recusou a service account "
                f"(status={response.status_code} body={response.text[:300]})"
            )
        token = response.json().get("access_token")
        if not token:
            raise GscAuthError("Token endpoint não devolveu access_token")
        return str(token)
    except httpx.HTTPError as exc:
        raise GscAuthError(f"Erro de rede ao obter access token: {exc}") from exc
    finally:
        if close:
            client.close()
