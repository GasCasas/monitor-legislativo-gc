import requests
from datetime import date, datetime
from typing import Optional

BASE_URL = "https://legis.senado.leg.br/dadosabertos"
TIMEOUT = 15
HEADERS = {"Accept": "application/json"}


def _get(url: str, params: dict = None) -> Optional[dict]:
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        return {"_erro": "Tempo de conexão esgotado com a API do Senado."}
    except requests.exceptions.HTTPError as e:
        return {"_erro": f"Erro HTTP {e.response.status_code}: recurso não encontrado."}
    except Exception as e:
        return {"_erro": str(e)}


def _buscar_situacao_atual(codigo: str) -> str:
    """Consulta o endpoint dedicado de situação atual da matéria."""
    url = f"{BASE_URL}/materia/situacaoatual/{codigo}.json"
    resp = _get(url)
    if not resp or "_erro" in resp:
        return "Situação não disponível."
    try:
        materia = (
            resp.get("SituacaoAtualMateria", {})
            .get("Materias", {})
            .get("Materia", {})
        )
        if isinstance(materia, list):
            materia = materia[0] if materia else {}

        autuacao = (
            materia.get("SituacaoAtual", {})
            .get("Autuacoes", {})
            .get("Autuacao", {})
        )
        if isinstance(autuacao, list):
            autuacao = autuacao[-1] if autuacao else {}

        situacoes = autuacao.get("Situacoes", {}).get("Situacao", {})
        if isinstance(situacoes, list):
            situacoes = situacoes[-1] if situacoes else {}

        descricao = situacoes.get("DescricaoSituacao", "")
        data_sit = situacoes.get("DataSituacao", "")

        local_nome = autuacao.get("NomeLocal", "")
        sigla_local = autuacao.get("SiglaLocal", "")
        local_str = f"{local_nome} ({sigla_local})" if local_nome and sigla_local else local_nome or sigla_local

        partes = [p for p in [descricao, local_str] if p]
        if data_sit:
            from datetime import datetime as dt
            try:
                data_fmt = dt.strptime(data_sit, "%Y-%m-%d").strftime("%d/%m/%Y")
                partes.append(f"em {data_fmt}")
            except ValueError:
                pass
        return " — ".join(partes) if partes else "Situação não disponível."
    except (KeyError, TypeError, AttributeError):
        return "Situação não disponível."


def buscar_materia(tipo: str, numero: str, ano: str) -> dict:
    """Retorna ementa, situação e link de uma matéria do Senado."""
    url = f"{BASE_URL}/materia/{tipo.upper()}/{numero}/{ano}.json"
    data = _get(url)
    if not data or "_erro" in data:
        return {"erro": data.get("_erro", "Matéria não encontrada.") if data else "Sem resposta da API."}

    try:
        materia = data["DetalheMateria"]["Materia"]

        # Ementa está em DadosBasicosMateria (não em IdentificacaoMateria)
        dados_basicos = materia.get("DadosBasicosMateria", {})
        ementa = dados_basicos.get("EmentaMateria", "")

        # Fallback para IdentificacaoMateria caso DadosBasicosMateria não tenha
        if not ementa:
            ementa = materia.get("IdentificacaoMateria", {}).get("EmentaMateria", "Ementa não disponível.")

        codigo = materia.get("IdentificacaoMateria", {}).get("CodigoMateria", "")
        link = f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{codigo}" if codigo else ""

        # Situação via endpoint dedicado
        situacao_txt = _buscar_situacao_atual(codigo) if codigo else "Situação não disponível."

        return {"ementa": ementa, "situacao": situacao_txt, "link": link, "codigo": codigo}
    except (KeyError, TypeError):
        return {"erro": "Estrutura de resposta inesperada da API do Senado."}


def buscar_votacoes_plenario(data_ref: date = None) -> list:
    """Retorna votações do plenário do Senado em uma data."""
    if data_ref is None:
        data_ref = date.today()
    data_str = data_ref.strftime("%Y%m%d")
    url = f"{BASE_URL}/plenario/lista/votacoes/{data_str}/{data_str}"
    resp = _get(url)
    if not resp or "_erro" in resp:
        return []

    try:
        votacoes = (
            resp.get("ListaVotacoes", {})
            .get("Votacoes", {})
            .get("Votacao", [])
        )
        if isinstance(votacoes, dict):
            votacoes = [votacoes]
        return votacoes or []
    except (KeyError, TypeError):
        return []


def buscar_agenda_plenario(data_ref: date = None) -> dict:
    """Retorna a agenda do plenário do Senado."""
    if data_ref is None:
        data_ref = date.today()
    data_str = data_ref.strftime("%Y%m%d")
    url = f"{BASE_URL}/plenario/agenda/{data_str}"
    resp = _get(url)
    if not resp or "_erro" in resp:
        return {}
    return resp


def buscar_pauta_comissao(sigla: str, data_ref: date = None) -> dict:
    """Retorna a pauta de uma comissão do Senado."""
    if data_ref is None:
        data_ref = date.today()
    data_str = data_ref.strftime("%Y%m%d")
    url = f"{BASE_URL}/comissao/agenda/{sigla.upper()}/{data_str}"
    resp = _get(url)
    if not resp or "_erro" in resp:
        return {}
    return resp


def buscar_reunioes_comissao(sigla: str, data_ref: date = None) -> list:
    """Retorna reuniões de uma comissão a partir da agenda."""
    if data_ref is None:
        data_ref = date.today()
    data_str = data_ref.strftime("%Y%m%d")
    url = f"{BASE_URL}/comissao/agenda/{sigla.upper()}/{data_str}"
    resp = _get(url)
    if not resp or "_erro" in resp:
        return []

    try:
        reunioes = (
            resp.get("AgendaReuniao", {})
            .get("Reunioes", {})
            .get("Reuniao", [])
        )
        if isinstance(reunioes, dict):
            reunioes = [reunioes]
        return reunioes or []
    except (KeyError, TypeError):
        return []


def buscar_mpvs_tramitando() -> list:
    """Retorna lista de Medidas Provisórias em tramitação no Senado."""
    url = f"{BASE_URL}/materia/pesquisa/lista"
    params = {"tipo": "MPV", "tramitando": "S", "v": "3"}
    resp = _get(url, params=params)
    if not resp or "_erro" in resp:
        return []

    try:
        materias = (
            resp.get("PesquisaBasicaMateria", {})
            .get("Materias", {})
            .get("Materia", [])
        )
        if isinstance(materias, dict):
            materias = [materias]
        return materias or []
    except (KeyError, TypeError):
        return []
