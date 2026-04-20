# Monitor Legislativo GC
### Gabinete do Senador Davi Alcolumbre — Senado Federal

Aplicativo Streamlit para acompanhamento de matérias legislativas e geração de briefings diários.

## Funcionalidades

### 📋 Monitoramento de Matérias
- Cadastro de proposições do Senado Federal e da Câmara dos Deputados
- Consulta automática às APIs abertas para obter ementa, situação atual e link oficial
- Lista salva em arquivo JSON local (`data/materias.json`)
- Filtro por casa legislativa

### 📰 Briefing Diário
- Votações do plenário do Senado Federal e da Câmara dos Deputados
- Pauta das comissões CCJ, CAE e CI do Senado
- Pauta das comissões CCJC, CFT e CINFRA da Câmara
- Medidas Provisórias em tramitação
- Seleção de data para consultas históricas

## Instalação

```bash
pip install -r requirements.txt
```

## Execução

```bash
streamlit run app.py
```

## Estrutura

```
monitor-legislativo-gc/
├── app.py                  # Aplicativo principal Streamlit
├── requirements.txt
├── README.md
├── modules/
│   ├── __init__.py
│   ├── senado.py           # Integração com API do Senado Federal
│   ├── camara.py           # Integração com API da Câmara dos Deputados
│   └── storage.py          # Gerenciamento do arquivo JSON local
└── data/
    └── materias.json       # Matérias monitoradas (persistência local)
```

## APIs utilizadas

- **Senado Federal:** https://legis.senado.leg.br/dadosabertos
- **Câmara dos Deputados:** https://dadosabertos.camara.leg.br/api/v2

## Paleta de cores

- Verde institucional: `#1a5276`
- Dourado: `#d4ac0d`
