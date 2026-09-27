import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import get_settings

_api_key_header = APIKeyHeader(
    name="X-API-Key",
    description="Chave interna compartilhada com a API principal (Estante API).",
    auto_error=False,
)


def verificar_api_key(api_key: str | None = Security(_api_key_header)) -> None:
    """Garante que apenas serviços autorizados consumam esta API."""
    if not api_key or not secrets.compare_digest(api_key, get_settings().api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API ausente ou inválida.",
        )
