import json
import uuid
from datetime import datetime
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "materias.json"


def carregar_materias() -> list:
    if not DATA_FILE.exists():
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text("[]", encoding="utf-8")
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def salvar_materias(materias: list) -> None:
    DATA_FILE.write_text(
        json.dumps(materias, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def adicionar_materia(casa: str, tipo: str, numero: str, ano: str, observacao: str) -> list:
    materias = carregar_materias()
    nova = {
        "id": str(uuid.uuid4()),
        "casa": casa.lower(),
        "tipo": tipo.upper().strip(),
        "numero": numero.strip(),
        "ano": ano.strip(),
        "observacao": observacao.strip(),
        "cadastrado_em": datetime.now().isoformat(),
    }
    materias.append(nova)
    salvar_materias(materias)
    return materias


def remover_materia(materia_id: str) -> list:
    materias = carregar_materias()
    materias = [m for m in materias if m["id"] != materia_id]
    salvar_materias(materias)
    return materias
