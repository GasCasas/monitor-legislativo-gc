"""
Persistência de matérias.

Prioridade: Supabase → arquivo local data/materias.json (fallback).

Mapeamento de campos:
  Local JSON   →  Supabase
  cadastrado_em → criado_em  (gerado automaticamente pelo banco)
  (novo) ementa, situacao, link — colunas extras na tabela
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


def _normalizar(registro: dict) -> dict:
    """Garante campos consistentes independente da origem (Supabase ou JSON)."""
    return {
        "id":            registro.get("id", ""),
        "casa":          registro.get("casa", ""),
        "tipo":          registro.get("tipo", ""),
        "numero":        registro.get("numero", ""),
        "ano":           registro.get("ano", ""),
        "observacao":    registro.get("observacao", ""),
        "ementa":        registro.get("ementa", ""),
        "situacao":      registro.get("situacao", ""),
        "link":          registro.get("link", ""),
        # suporte a ambos os nomes de campo de data
        "cadastrado_em": registro.get("criado_em") or registro.get("cadastrado_em", ""),
    }


# ─── API pública ──────────────────────────────────────────────────────────────

def carregar_materias() -> list:
    """Retorna a lista de matérias (Supabase ou JSON local)."""
    try:
        from modules import database as db
        if db.disponivel():
            dados = db.listar_materias()
            if dados is not None:
                return [_normalizar(m) for m in dados]
    except Exception:
        pass
    return _carregar_local()


def adicionar_materia(
    casa: str, tipo: str, numero: str, ano: str, observacao: str
) -> list:
    """Insere nova matéria e retorna a lista atualizada."""
    nova = {
        "id":            str(uuid.uuid4()),
        "casa":          casa.lower(),
        "tipo":          tipo.upper().strip(),
        "numero":        numero.strip(),
        "ano":           ano.strip(),
        "observacao":    observacao.strip(),
        "ementa":        "",
        "situacao":      "",
        "link":          "",
        "cadastrado_em": datetime.now().isoformat(),
    }

    try:
        from modules import database as db
        if db.disponivel():
            db.inserir_materia(nova)
            return [_normalizar(m) for m in db.listar_materias()]
    except Exception:
        pass

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
            return [_normalizar(m) for m in db.listar_materias()]
    except Exception:
        pass

    materias = _carregar_local()
    materias = [m for m in materias if m["id"] != materia_id]
    _salvar_local(materias)
    return materias


def salvar_materias(materias: list) -> None:
    """Sobrescreve a lista completa (fallback local apenas)."""
    _salvar_local(materias)
