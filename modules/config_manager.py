"""
Persistência de configurações.

Prioridade: Supabase → arquivo local data/config.json (fallback).
"""

from __future__ import annotations

import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent.parent / "data" / "config.json"

DEFAULT_CONFIG = {
    "email_destino": "",
    "email_remetente": "",
    "email_senha_app": "",
    "celular_whatsapp": "",
    "callmebot_apikey": "",
    "horario_briefing": "07:00",
}


# ─── JSON local ───────────────────────────────────────────────────────────────

def _carregar_local() -> dict:
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    try:
        dados = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        config = DEFAULT_CONFIG.copy()
        config.update(dados)
        return config
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CONFIG.copy()


def _salvar_local(config: dict) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ─── API pública ──────────────────────────────────────────────────────────────

def carregar_config() -> dict:
    """Lê configurações do Supabase ou do arquivo local (fallback)."""
    try:
        from modules import database as db
        if db.disponivel():
            return db.ler_configuracoes()
    except Exception:
        pass
    return _carregar_local()


def salvar_config(config: dict) -> None:
    """Salva configurações no Supabase e também no arquivo local (backup)."""
    # Sempre persiste localmente como backup offline
    _salvar_local(config)

    try:
        from modules import database as db
        if db.disponivel():
            db.salvar_configuracoes(config)
    except Exception:
        pass
