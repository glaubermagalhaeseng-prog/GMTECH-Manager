
import hashlib
from fastapi import Request
from fastapi.responses import RedirectResponse

from app.database import conectar


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def empresa_id_sessao(request: Request) -> int:
    return int(request.session.get("empresa_id") or 1)


def usuario_logado(request: Request):
    return request.session.get("usuario")


def exigir_login(request: Request):
    if not request.session.get("usuario"):
        return RedirectResponse("/login", status_code=303)
    return None
