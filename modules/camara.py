import requests
from datetime import date
from typing import Optional

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
TIMEOUT = 15
HEADERS = {"Accept": "application/json"}

# Mapeamento de siglas internas → siglas usadas pela API da Câmara
COMISSOES_CAMARA = {
    "CCJ": "CCJC",   # Constituição, Justiça e Cidadania
    "CAE": "CFT",    # Finanças e Tributação (equivalente econômico na Câmara)
    "CI": "CINFRA",  # Infraestrutura
}


def _get(url: str, params: dict = None) -> Optional[dict]:
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        return {"_erro": "Tempo de conexão esgotado com a API da Câmara."}
    except requests.exceptions.HTTPError as e:
        return {"_erro": f"Erro HTTP {e.response.status_code}: recurso não encontrado."}
    except Exception as e:
        return {"_erro": str(e)}


def buscar_proposicao(tipo: str, numero: str, ano: str) -> dict:
    """Retorna ementa, situação e link de uma proposição da Câmara."""
    url = f"{BASE_URL}/proposicoes"
    params = {
        "siglaTipo": tipo.upper(),
        "numero": numero,
        "ano": ano,
        "itens": 1,
    }
    resp = _get(url, params=params)
    if not resp or "_erro" in resp:
        return {"erro": resp.get("_erro", "Sem resposta da API.") if resp else "Sem resposta."}

    dados = resp.get("dados", [])
    if not dados:
        return {"erro": "Proposição não encontrada na API da Câmara."}

    prop = dados[0]
    prop_id = prop.get("id")

    # Busca detalhes completos
    detalhe = _get(f"{BASE_URL}/proposicoes/{prop_id}")
    if detalhe and "dados" in detalhe:
        d = detalhe["dados"]
        ementa = d.get("ementa", prop.get("ementa", "Ementa não disponível."))
        situacao = d.get("statusProposicao", {})
        situacao_txt = situacao.get("descricaoSituacao", "Situação não disponível.")
        orgao = situacao.get("siglaOrgao", "")
        if orgao:
            situacao_txt = f"{situacao_txt} — {orgao}"
        uri_prop = d.get("urlInteiroTeor") or f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={prop_id}"
        return {
            "ementa": ementa,
            "situacao": situacao_txt,
            "link": f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={prop_id}",
            "id": prop_id,
        }

    return {
        "ementa": prop.get("ementa", "Ementa não disponível."),
        "situacao": "Situação não disponível.",
        "link": f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={prop_id}",
        "id": prop_id,
    }


def buscar_votacoes_plenario(data_ref: date = None) -> list:
    """Retorna votações do plenário da Câmara em uma data."""
    if data_ref is None:
        data_ref = date.today()
    data_str = data_ref.strftime("%Y-%m-%d")
    url = f"{BASE_URL}/votacoes"
    params = {
        "dataInicio": data_str,
        "dataFim": data_str,
        "ordenarPor": "dataHoraRegistro",
        "ordem": "DESC",
        "itens": 50,
    }
    resp = _get(url, params=params)
    if not resp or "_erro" in resp:
        return []
    return resp.get("dados", [])


def _buscar_id_orgao(sigla: str) -> Optional[int]:
    """Busca o ID de um órgão (comissão) pelo nome/sigla."""
    url = f"{BASE_URL}/orgaos"
    params = {"sigla": sigla, "itens": 5}
    resp = _get(url, params=params)
    if not resp or "_erro" in resp:
        return None
    dados = resp.get("dados", [])
    if dados:
        return dados[0].get("id")
    return None


def buscar_pauta_comissao(sigla_interna: str, data_ref: date = None) -> list:
    """Retorna eventos (reuniões) de uma comissão da Câmara em uma data."""
    if data_ref is None:
        data_ref = date.today()
    data_str = data_ref.strftime("%Y-%m-%d")

    sigla_api = COMISSOES_CAMARA.get(sigla_interna.upper(), sigla_interna.upper())
    orgao_id = _buscar_id_orgao(sigla_api)
    if not orgao_id:
        return []

    url = f"{BASE_URL}/orgaos/{orgao_id}/eventos"
    params = {
        "dataInicio": data_str,
        "dataFim": data_str,
        "itens": 20,
    }
    resp = _get(url, params=params)
    if not resp or "_erro" in resp:
        return []

    eventos = resp.get("dados", [])
    resultado = []
    for ev in eventos:
        resultado.append({
            "titulo": ev.get("descricaoTipo", "Reunião"),
            "hora": ev.get("dataHoraInicio", "")[:16].replace("T", " ") if ev.get("dataHoraInicio") else "–",
            "situacao": ev.get("situacao", "–"),
            "local": ev.get("localCamara", {}).get("nome", "–") if ev.get("localCamara") else "–",
            "uri": ev.get("uri", ""),
        })
    return resultado


def buscar_eventos_comissao_por_id(orgao_id: int, data_ref: date = None) -> list:
    if data_ref is None:
        data_ref = date.today()
    data_str = data_ref.strftime("%Y-%m-%d")
    url = f"{BASE_URL}/orgaos/{orgao_id}/eventos"
    params = {"dataInicio": data_str, "dataFim": data_str, "itens": 20}
    resp = _get(url, params=params)
    if not resp or "_erro" in resp:
        return []
    return resp.get("dados", [])
