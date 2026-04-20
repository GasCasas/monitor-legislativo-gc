"""
Persistência de matérias.

Prioridade: Supabase → arquivo local data/materias.json (fallback).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "materias.json"


# ─── JSON local ───────────────────────────────────────────────────────────────

def _carregar_local() -> list:
    if not DATA_FILE.exists():
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text("[]", encoding="utf-8")
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _salvar_local(materias: list) -> None:
    DATA_FILE.write_text(
        json.dumps(materias, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ─── API pública ──────────────────────────────────────────────────────────────

def carregar_materias() -> list:
    """Retorna a lista de matérias (Supabase ou JSON local)."""
    try:
        from modules import database as db
        if db.disponivel():
            dados = db.listar_materias()
            if dados is not None:
                return dados
    except Exception:
        pass
    return _carregar_local()


def adicionar_materia(
    casa: str, tipo: str, numero: str, ano: str, observacao: str
) -> list:
    """Insere nova matéria e retorna a lista atualizada."""
    nova = {
        "id": str(uuid.uuid4()),
        "casa": casa.lower(),
        "tipo": tipo.upper().strip(),
        "numero": numero.strip(),
        "ano": ano.strip(),
        "observacao": observacao.strip(),
        "cadastrado_em": datetime.now().isoformat(),
    }

    try:
        from modules import database as db
        if db.disponivel():
            db.inserir_materia(nova)
            return db.listar_materias()
    except Exception:
        pass

    # Fallback local
    materias = _carregar_local()
    materias.append(nova)
    _salvar_local(materias)
    return materias


def remover_materia(materia_id: str) -> list:
    """Remove matéria pelo id e retorna a lista atualizada."""
    try:
        from modules import database as db
        if db.disponivel():
            db.deletar_materia(materia_id)
            return db.listar_materias()
    except Exception:
        pass

    # Fallback local
    materias = _carregar_local()
    materias = [m for m in materias if m["id"] != materia_id]
    _salvar_local(materias)
    return materias


def salvar_materias(materias: list) -> None:
    """Sobrescreve a lista completa (usado apenas pelo fallback local)."""
    _salvar_local(materias)
