"""
Camada de acesso ao Supabase.

Tabelas esperadas:
  materias     — id uuid PK, casa text, tipo text, numero text, ano text,
                  observacao text, cadastrado_em timestamptz
  configuracoes — chave text PK, valor text
"""

from __future__ import annotations

import streamlit as st
from typing import Optional

# ─── Credenciais (lidas de st.secrets / secrets.toml) ─────────────────────────
def _credenciais() -> tuple[str, str]:
    try:
        cfg = st.secrets["supabase"]
        return cfg["url"], cfg["key"]
    except Exception:
        return "", ""


@st.cache_resource(show_spinner=False)
def _cliente():
    """Retorna o cliente Supabase (singleton cacheado pelo Streamlit)."""
    url, key = _credenciais()
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception:
        return None


def disponivel() -> bool:
    """Retorna True se o Supabase está configurado e acessível."""
    return _cliente() is not None


# ══════════════════════════════════════════════════════════════════════════════
# CRUD — tabela materias
# ══════════════════════════════════════════════════════════════════════════════

def listar_materias() -> list:
    """Retorna todas as matérias ordenadas por data de cadastro."""
    cli = _cliente()
    if cli is None:
        return []
    try:
        res = cli.table("materias").select("*").order("cadastrado_em").execute()
        return res.data or []
    except Exception:
        return []


def inserir_materia(mat: dict) -> Optional[dict]:
    """Insere uma matéria e retorna o registro criado."""
    cli = _cliente()
    if cli is None:
        return None
    try:
        res = cli.table("materias").insert(mat).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def deletar_materia(materia_id: str) -> bool:
    """Remove uma matéria pelo id. Retorna True se bem-sucedido."""
    cli = _cliente()
    if cli is None:
        return False
    try:
        cli.table("materias").delete().eq("id", materia_id).execute()
        return True
    except Exception:
        return False


def atualizar_materia(materia_id: str, campos: dict) -> Optional[dict]:
    """Atualiza campos de uma matéria. Retorna o registro atualizado."""
    cli = _cliente()
    if cli is None:
        return None
    try:
        res = cli.table("materias").update(campos).eq("id", materia_id).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# CRUD — tabela configuracoes  (modelo chave/valor)
# ══════════════════════════════════════════════════════════════════════════════

_CONFIG_DEFAULTS = {
    "email_destino": "",
    "email_remetente": "",
    "email_senha_app": "",
    "celular_whatsapp": "",
    "callmebot_apikey": "",
    "horario_briefing": "07:00",
}


def ler_configuracoes() -> dict:
    """Lê todas as configurações e retorna como dict. Inclui defaults."""
    cli = _cliente()
    config = _CONFIG_DEFAULTS.copy()
    if cli is None:
        return config
    try:
        res = cli.table("configuracoes").select("chave, valor").execute()
        for row in (res.data or []):
            config[row["chave"]] = row["valor"]
        return config
    except Exception:
        return config


def salvar_configuracoes(config: dict) -> bool:
    """Persiste o dict de configurações via upsert. Retorna True se OK."""
    cli = _cliente()
    if cli is None:
        return False
    try:
        registros = [{"chave": k, "valor": str(v)} for k, v in config.items()]
        cli.table("configuracoes").upsert(registros, on_conflict="chave").execute()
        return True
    except Exception:
        return False


def salvar_configuracao(chave: str, valor: str) -> bool:
    """Persiste uma única configuração chave/valor."""
    cli = _cliente()
    if cli is None:
        return False
    try:
        cli.table("configuracoes").upsert(
            {"chave": chave, "valor": valor}, on_conflict="chave"
        ).execute()
        return True
    except Exception:
        return False
