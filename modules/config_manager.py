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


def carregar_config() -> dict:
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    try:
        dados = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        config = DEFAULT_CONFIG.copy()
        config.update(dados)
        return config
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CONFIG.copy()


def salvar_config(config: dict) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
