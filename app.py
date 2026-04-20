import streamlit as st
from datetime import date, datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules import storage, senado, camara, config_manager, notifications

# ─── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Monitor Legislativo GC",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Estilos CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    :root {
        --verde: #1a5276;
        --dourado: #d4ac0d;
        --verde-claro: #2e86c1;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a5276 0%, #154360 100%) !important;
    }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] .stRadio label { font-size: 15px !important; }
    [data-testid="stSidebar"] hr { border-color: #d4ac0d !important; }

    .header-box {
        background: linear-gradient(90deg, #1a5276 60%, #154360 100%);
        color: white; padding: 18px 28px; border-radius: 10px;
        margin-bottom: 24px; border-left: 6px solid #d4ac0d;
    }
    .header-box h1 { margin: 0; font-size: 1.7rem; }
    .header-box p  { margin: 4px 0 0 0; opacity: 0.85; font-size: 0.95rem; }

    .materia-card {
        background: #f4f6f8; border: 1px solid #d5d8dc;
        border-left: 5px solid #1a5276; border-radius: 8px;
        padding: 14px 18px; margin-bottom: 14px;
    }
    .materia-card h4 { margin: 0 0 6px 0; color: #1a5276; font-size: 1rem; }
    .materia-card .ementa { font-size: 0.88rem; color: #333; margin-bottom: 6px; }
    .materia-card .situacao { font-size: 0.82rem; color: #555; }
    .materia-card .obs { font-size: 0.8rem; color: #888; font-style: italic; margin-top: 4px; }

    .badge-senado {
        background: #1a5276; color: white;
        padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: bold;
        display: inline-block; margin-right: 6px;
    }
    .badge-camara {
        background: #196f3d; color: white;
        padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: bold;
        display: inline-block; margin-right: 6px;
    }
    .badge-tipo {
        background: #d4ac0d; color: #1a1a1a;
        padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: bold;
        display: inline-block;
    }

    .briefing-header {
        background: #1a5276; color: white; padding: 10px 18px;
        border-radius: 8px 8px 0 0; font-weight: bold; font-size: 1rem; margin-top: 20px;
    }
    .briefing-body {
        background: #f4f6f8; border: 1px solid #d5d8dc; border-top: none;
        border-radius: 0 0 8px 8px; padding: 14px 18px; margin-bottom: 4px;
    }
    .briefing-item {
        border-left: 3px solid #d4ac0d; padding-left: 12px;
        margin-bottom: 10px; font-size: 0.9rem;
    }
    .briefing-item strong { color: #1a5276; }

    .stButton > button {
        background-color: #1a5276 !important; color: white !important;
        border: none !important; border-radius: 6px !important; font-weight: 600 !important;
    }
    .stButton > button:hover {
        background-color: #154360 !important; border: 1px solid #d4ac0d !important;
    }
    div[data-testid="stForm"] button[type="submit"] {
        background-color: #d4ac0d !important; color: #1a1a1a !important;
    }

    .divisor-dourado { border: none; border-top: 2px solid #d4ac0d; margin: 20px 0; }

    .info-box {
        background: #eaf4fb; border-left: 4px solid #2e86c1; padding: 10px 16px;
        border-radius: 4px; font-size: 0.88rem; color: #1a5276; margin-bottom: 12px;
    }
    .erro-box {
        background: #fdfefe; border-left: 4px solid #e74c3c; padding: 10px 16px;
        border-radius: 4px; font-size: 0.88rem; color: #922b21; margin-bottom: 8px;
    }
    .config-section {
        background: #f4f6f8; border: 1px solid #d5d8dc; border-radius: 8px;
        padding: 18px 22px; margin-bottom: 18px;
    }
    .config-section h3 { color: #1a5276; margin: 0 0 14px 0; font-size: 1rem; }

    .callmebot-instructions {
        background: #fffbe6; border: 1px solid #d4ac0d; border-left: 4px solid #d4ac0d;
        border-radius: 6px; padding: 14px 18px; margin-bottom: 14px; font-size: 0.88rem;
    }
    .callmebot-instructions h4 { color: #7d6608; margin: 0 0 8px 0; font-size: 0.95rem; }
    .callmebot-instructions ol { margin: 0; padding-left: 18px; color: #555; line-height: 1.8; }
    .callmebot-instructions code {
        background: #fff3cd; padding: 1px 5px; border-radius: 3px;
        font-size: 0.85rem; color: #333;
    }
</style>
""", unsafe_allow_html=True)


# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚖️ Monitor Legislativo GC")
    st.markdown("**Gabinete do Senador**")
    st.markdown("**Davi Alcolumbre**")
    st.markdown("---")
    pagina = st.radio(
        "Navegação",
        ["📋 Monitoramento de Matérias", "📰 Briefing Diário", "⚙️ Configurações"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown(
        "<small style='opacity:0.7'>Senado Federal &amp; Câmara dos Deputados<br>"
        "APIs Abertas • Dados Públicos</small>",
        unsafe_allow_html=True,
    )


# ─── Helper: busca dados de todas as matérias cadastradas ─────────────────────
def _coletar_dados_materias(materias: list) -> list:
    resultado = []
    for mat in materias:
        if mat["casa"] == "senado":
            dados = senado.buscar_materia(mat["tipo"], mat["numero"], mat["ano"])
        else:
            dados = camara.buscar_proposicao(mat["tipo"], mat["numero"], mat["ano"])
        resultado.append({"materia": mat, "dados": dados})
    return resultado


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — MONITORAMENTO DE MATÉRIAS
# ══════════════════════════════════════════════════════════════════════════════
if pagina == "📋 Monitoramento de Matérias":

    st.markdown("""
    <div class="header-box">
        <h1>📋 Monitoramento de Matérias</h1>
        <p>Acompanhe proposições do Senado Federal e da Câmara dos Deputados em tempo real.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Formulário de cadastro ────────────────────────────────────────────────
    with st.expander("➕ Cadastrar nova matéria", expanded=False):
        with st.form("form_cadastro", clear_on_submit=True):
            col1, col2 = st.columns([1, 1])
            with col1:
                casa = st.selectbox("Casa Legislativa", ["Senado Federal", "Câmara dos Deputados"])
            with col2:
                tipo_opcoes_senado = ["PL", "PEC", "PLP", "MPV", "PDL", "PDS", "RES", "MSF", "SF", "REQ"]
                tipo_opcoes_camara = ["PL", "PEC", "PLP", "MPV", "PDL", "PDS", "REQ", "PRC", "INC"]
                tipo = st.selectbox(
                    "Tipo",
                    tipo_opcoes_senado if casa == "Senado Federal" else tipo_opcoes_camara,
                )
            col3, col4 = st.columns([1, 1])
            with col3:
                numero = st.text_input("Número", placeholder="ex: 1234")
            with col4:
                ano = st.text_input("Ano", value=str(date.today().year), placeholder="ex: 2024")
            observacao = st.text_area("Observação (opcional)", placeholder="Notas internas do gabinete...", height=80)
            submitted = st.form_submit_button("💾 Salvar Matéria", use_container_width=True)
            if submitted:
                if not numero or not ano:
                    st.error("Preencha o número e o ano da matéria.")
                else:
                    storage.adicionar_materia(
                        casa="senado" if casa == "Senado Federal" else "camara",
                        tipo=tipo, numero=numero, ano=ano, observacao=observacao,
                    )
                    st.success(f"✅ {tipo} {numero}/{ano} cadastrado com sucesso!")
                    st.rerun()

    st.markdown("<hr class='divisor-dourado'>", unsafe_allow_html=True)

    # ── Barra de ações ────────────────────────────────────────────────────────
    materias = storage.carregar_materias()
    config = config_manager.carregar_config()

    col_titulo, col_email, col_wpp, col_reload = st.columns([3, 1.3, 1.3, 1])
    with col_titulo:
        st.markdown(f"### 📌 Matérias Monitoradas ({len(materias)})")
    with col_email:
        btn_email = st.button("📧 Enviar por e-mail", use_container_width=True, disabled=not materias)
    with col_wpp:
        btn_wpp = st.button("📱 Enviar via WhatsApp", use_container_width=True, disabled=not materias)
    with col_reload:
        st.button("🔄 Atualizar", use_container_width=True)

    # ── Envio por e-mail ──────────────────────────────────────────────────────
    if btn_email:
        if not config.get("email_remetente") or not config.get("email_senha_app"):
            st.warning("⚠️ Configure o e-mail remetente e a Senha de App do Gmail em **⚙️ Configurações**.")
        elif not config.get("email_destino"):
            st.warning("⚠️ Configure o e-mail de destino em **⚙️ Configurações**.")
        else:
            with st.spinner("Consultando APIs e enviando e-mail…"):
                dados_materias = _coletar_dados_materias(materias)
                assunto = f"Monitor Legislativo GC — Alerta de Matérias ({date.today().strftime('%d/%m/%Y')})"
                ok, msg = notifications.enviar_email(
                    remetente=config["email_remetente"],
                    senha_app=config["email_senha_app"],
                    destinatario=config["email_destino"],
                    assunto=assunto,
                    materias_com_dados=dados_materias,
                )
            if ok:
                st.success(f"✅ {msg} Enviado para: {config['email_destino']}")
            else:
                st.error(f"❌ {msg}")

    # ── Envio por WhatsApp ────────────────────────────────────────────────────
    if btn_wpp:
        if not config.get("celular_whatsapp"):
            st.warning("⚠️ Configure o celular para WhatsApp em **⚙️ Configurações**.")
        elif not config.get("callmebot_apikey"):
            st.warning("⚠️ Configure a API Key do CallMeBot em **⚙️ Configurações**.")
        else:
            with st.spinner("Consultando APIs e enviando WhatsApp…"):
                dados_materias = _coletar_dados_materias(materias)
                ok, msg = notifications.enviar_whatsapp(
                    celular=config["celular_whatsapp"],
                    apikey=config["callmebot_apikey"],
                    materias_com_dados=dados_materias,
                )
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")

    # ── Lista de matérias ─────────────────────────────────────────────────────
    if not materias:
        st.markdown("""
        <div class="info-box">
            Nenhuma matéria cadastrada. Use o formulário acima para adicionar proposições.
        </div>
        """, unsafe_allow_html=True)
    else:
        filtro_casa = st.radio(
            "Filtrar por casa:",
            ["Todas", "Senado Federal", "Câmara dos Deputados"],
            horizontal=True,
        )

        for mat in materias:
            if filtro_casa == "Senado Federal" and mat["casa"] != "senado":
                continue
            if filtro_casa == "Câmara dos Deputados" and mat["casa"] != "camara":
                continue

            badge_casa = (
                '<span class="badge-senado">SENADO</span>'
                if mat["casa"] == "senado"
                else '<span class="badge-camara">CÂMARA</span>'
            )
            badge_tipo = f'<span class="badge-tipo">{mat["tipo"]} {mat["numero"]}/{mat["ano"]}</span>'

            if mat["casa"] == "senado":
                dados = senado.buscar_materia(mat["tipo"], mat["numero"], mat["ano"])
            else:
                dados = camara.buscar_proposicao(mat["tipo"], mat["numero"], mat["ano"])

            tem_erro = "erro" in dados

            ementa_html = (
                f'<div class="ementa">📄 {dados["ementa"]}</div>'
                if not tem_erro
                else f'<div class="erro-box">⚠️ {dados["erro"]}</div>'
            )
            situacao_html = (
                f'<div class="situacao">🔹 <strong>Situação:</strong> {dados["situacao"]}</div>'
                if not tem_erro else ""
            )
            link_html = (
                f'<div style="margin-top:6px"><a href="{dados["link"]}" target="_blank" '
                f'style="color:#1a5276;font-size:0.82rem;">🔗 Ver no site oficial</a></div>'
                if not tem_erro and dados.get("link") else ""
            )
            obs_html = (
                f'<div class="obs">📝 Obs: {mat["observacao"]}</div>'
                if mat.get("observacao") else ""
            )

            col_card, col_del = st.columns([11, 1])
            with col_card:
                st.markdown(f"""
                <div class="materia-card">
                    <h4>{badge_casa} {badge_tipo}</h4>
                    {ementa_html}{situacao_html}{link_html}{obs_html}
                </div>
                """, unsafe_allow_html=True)
            with col_del:
                if st.button("🗑️", key=f"del_{mat['id']}", help="Remover matéria"):
                    storage.remover_materia(mat["id"])
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — BRIEFING DIÁRIO
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "📰 Briefing Diário":

    st.markdown("""
    <div class="header-box">
        <h1>📰 Briefing Legislativo Diário</h1>
        <p>Votações, pautas de comissões e Medidas Provisórias em tramitação.</p>
    </div>
    """, unsafe_allow_html=True)

    col_data, col_btn = st.columns([2, 1])
    with col_data:
        data_briefing = st.date_input(
            "Data do Briefing", value=date.today(),
            max_value=date.today(), format="DD/MM/YYYY",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        gerar = st.button("⚡ Gerar Briefing", use_container_width=True)

    if gerar or "briefing_gerado" in st.session_state:
        if gerar:
            st.session_state["briefing_data"] = data_briefing
            st.session_state["briefing_gerado"] = True

        data_ref = st.session_state.get("briefing_data", data_briefing)
        data_fmt = data_ref.strftime("%d/%m/%Y")
        dia_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
                      "Sexta-feira", "Sábado", "Domingo"][data_ref.weekday()]

        st.markdown(f"""
        <div style="background:#eaf4fb;border-left:4px solid #d4ac0d;padding:12px 18px;
                    border-radius:6px;margin-bottom:18px;">
            <strong style="color:#1a5276;font-size:1.05rem;">
                📅 Briefing de {dia_semana}, {data_fmt}
            </strong><br>
            <small style="color:#555">Gabinete do Senador Davi Alcolumbre • Senado Federal</small>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner("Consultando APIs do Senado e da Câmara…"):

            # 1. Votações Plenário Senado
            st.markdown('<div class="briefing-header">🏛️ Votações do Plenário — Senado Federal</div>', unsafe_allow_html=True)
            votacoes_sf = senado.buscar_votacoes_plenario(data_ref)
            body_html = ""
            if votacoes_sf:
                for v in votacoes_sf[:15]:
                    descricao = v.get("DescricaoVotacao") or v.get("Materia", {}).get("EmentaMateria", "Votação sem descrição")
                    mat_v = v.get("Materia", {})
                    sigla = mat_v.get("SiglaMateria", "")
                    num = mat_v.get("NumeroMateria", "")
                    ano_v = mat_v.get("AnoMateria", "")
                    resultado = v.get("DescricaoResultado", "–")
                    identificacao = f"{sigla} {num}/{ano_v}" if sigla else "–"
                    body_html += f"""
                    <div class="briefing-item">
                        <strong>{identificacao}</strong> — {resultado}<br>
                        <span style="color:#555">{str(descricao)[:180]}{"…" if len(str(descricao)) > 180 else ""}</span>
                    </div>"""
            else:
                body_html = "<div class='info-box'>Nenhuma votação registrada no Senado para esta data.</div>"
            st.markdown(f'<div class="briefing-body">{body_html}</div>', unsafe_allow_html=True)

            # 2. Votações Plenário Câmara
            st.markdown('<div class="briefing-header">🏛️ Votações do Plenário — Câmara dos Deputados</div>', unsafe_allow_html=True)
            votacoes_cd = camara.buscar_votacoes_plenario(data_ref)
            body_html = ""
            if votacoes_cd:
                for v in votacoes_cd[:15]:
                    descricao = v.get("descricao") or v.get("proposicaoObjeto", "Votação sem descrição")
                    aprovacao = v.get("aprovacao")
                    resultado = "✅ Aprovada" if aprovacao == 1 else ("❌ Rejeitada" if aprovacao == 0 else "–")
                    hora = v.get("dataHoraRegistro", "")[:16].replace("T", " ") if v.get("dataHoraRegistro") else "–"
                    body_html += f"""
                    <div class="briefing-item">
                        <strong>{hora}</strong> — {resultado}<br>
                        <span style="color:#555">{str(descricao)[:180]}{"…" if len(str(descricao)) > 180 else ""}</span>
                    </div>"""
            else:
                body_html = "<div class='info-box'>Nenhuma votação registrada na Câmara para esta data.</div>"
            st.markdown(f'<div class="briefing-body">{body_html}</div>', unsafe_allow_html=True)

            # 3. Comissões Senado
            for sigla_com, nome_com in [
                ("CCJ", "Comissão de Constituição e Justiça"),
                ("CAE", "Comissão de Assuntos Econômicos"),
                ("CI", "Comissão de Infraestrutura"),
            ]:
                st.markdown(f'<div class="briefing-header">🏢 {sigla_com} — {nome_com} (Senado)</div>', unsafe_allow_html=True)
                reunioes = senado.buscar_reunioes_comissao(sigla_com, data_ref)
                body_html = ""
                if reunioes:
                    for r in reunioes:
                        titulo = r.get("DescricaoReuniao") or r.get("TipoReuniao", {}).get("DescricaoTipoReuniao", "Reunião")
                        hora_r = r.get("HoraInicioReuniao", "–")
                        local_r = r.get("Local", {}).get("NomeLocal", "–") if isinstance(r.get("Local"), dict) else "–"
                        situacao_r = r.get("SituacaoReuniao", {}).get("DescricaoSituacaoReuniao", "–") if isinstance(r.get("SituacaoReuniao"), dict) else "–"
                        pauta_items = r.get("Pautas", {}).get("Pauta", []) if isinstance(r.get("Pautas"), dict) else []
                        if isinstance(pauta_items, dict):
                            pauta_items = [pauta_items]
                        pautas_html = ""
                        for p in pauta_items[:5]:
                            mat_p = p.get("Materia", {})
                            sm = mat_p.get("SiglaMateria", "")
                            nm = mat_p.get("NumeroMateria", "")
                            am = mat_p.get("AnoMateria", "")
                            em = mat_p.get("EmentaMateria", "")
                            if sm:
                                pautas_html += f"<br>&nbsp;&nbsp;&nbsp;• <strong>{sm} {nm}/{am}</strong>: {em[:120]}{'…' if len(em) > 120 else ''}"
                        body_html += f"""
                        <div class="briefing-item">
                            <strong>🕐 {hora_r}</strong> | {local_r} | Situação: {situacao_r}<br>
                            <span style="color:#555">{titulo}</span>{pautas_html}
                        </div>"""
                else:
                    body_html = f"<div class='info-box'>Sem reuniões do {sigla_com} registradas para esta data.</div>"
                st.markdown(f'<div class="briefing-body">{body_html}</div>', unsafe_allow_html=True)

            # 4. Comissões Câmara
            for sigla_int, sigla_api, nome_com in [
                ("CCJ", "CCJC", "Comissão de Constituição e Justiça e de Cidadania"),
                ("CAE", "CFT", "Comissão de Finanças e Tributação"),
                ("CI", "CINFRA", "Comissão de Infraestrutura"),
            ]:
                st.markdown(f'<div class="briefing-header">🏢 {sigla_api} — {nome_com} (Câmara)</div>', unsafe_allow_html=True)
                eventos = camara.buscar_pauta_comissao(sigla_int, data_ref)
                body_html = ""
                if eventos:
                    for ev in eventos:
                        body_html += f"""
                        <div class="briefing-item">
                            <strong>🕐 {ev["hora"]}</strong> | {ev["local"]} | {ev["situacao"]}<br>
                            <span style="color:#555">{ev["titulo"]}</span>
                        </div>"""
                else:
                    body_html = f"<div class='info-box'>Sem eventos de {sigla_api} registrados para esta data.</div>"
                st.markdown(f'<div class="briefing-body">{body_html}</div>', unsafe_allow_html=True)

            # 5. MPVs em tramitação
            st.markdown('<div class="briefing-header">⚡ Medidas Provisórias em Tramitação — Senado Federal</div>', unsafe_allow_html=True)
            mpvs = senado.buscar_mpvs_tramitando()
            body_html = ""
            if mpvs:
                for mpv in mpvs[:20]:
                    ident = mpv.get("IdentificacaoMateria", {})
                    sigla_mpv = ident.get("SiglaSubtipoMateria", ident.get("SiglaMateria", "MPV"))
                    num_mpv = ident.get("NumeroMateria", "–")
                    ano_mpv = ident.get("AnoMateria", "–")
                    ementa_mpv = ident.get("EmentaMateria", "Ementa não disponível.")
                    cod_mpv = ident.get("CodigoMateria", "")
                    link_mpv = f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{cod_mpv}" if cod_mpv else ""
                    link_tag = f' — <a href="{link_mpv}" target="_blank" style="color:#1a5276;font-size:0.8rem;">🔗 ver</a>' if link_mpv else ""
                    body_html += f"""
                    <div class="briefing-item">
                        <strong>{sigla_mpv} {num_mpv}/{ano_mpv}</strong>{link_tag}<br>
                        <span style="color:#555">{ementa_mpv[:200]}{"…" if len(ementa_mpv) > 200 else ""}</span>
                    </div>"""
            else:
                body_html = "<div class='info-box'>Nenhuma MPV em tramitação encontrada.</div>"
            st.markdown(f'<div class="briefing-body">{body_html}</div>', unsafe_allow_html=True)

        st.markdown("<hr class='divisor-dourado'>", unsafe_allow_html=True)
        st.markdown(
            f"<small style='color:#888'>Briefing gerado em {date.today().strftime('%d/%m/%Y')} "
            f"via APIs Abertas do Senado Federal e Câmara dos Deputados.</small>",
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "⚙️ Configurações":

    st.markdown("""
    <div class="header-box">
        <h1>⚙️ Configurações</h1>
        <p>Gerencie alertas por e-mail e WhatsApp para o monitoramento legislativo.</p>
    </div>
    """, unsafe_allow_html=True)

    config = config_manager.carregar_config()

    with st.form("form_config"):

        # ── Seção 1: E-mail ───────────────────────────────────────────────────
        st.markdown("""
        <div style="background:#1a5276;color:white;padding:10px 18px;border-radius:8px 8px 0 0;
                    font-weight:bold;font-size:1rem;">
            📧 Alertas por E-mail (Gmail)
        </div>
        <div style="background:#f4f6f8;border:1px solid #d5d8dc;border-top:none;
                    border-radius:0 0 8px 8px;padding:18px 22px;margin-bottom:18px;">
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            email_destino = st.text_input(
                "📬 E-mail para receber alertas",
                value=config.get("email_destino", ""),
                placeholder="destinatario@exemplo.com",
                help="Endereço que receberá os alertas.",
            )
        with col2:
            email_remetente = st.text_input(
                "📤 E-mail remetente (conta Gmail)",
                value=config.get("email_remetente", ""),
                placeholder="seugmail@gmail.com",
                help="Conta Gmail usada para enviar. Precisa ter Senha de App ativada.",
            )

        email_senha_app = st.text_input(
            "🔑 Senha de App do Gmail",
            value=config.get("email_senha_app", ""),
            type="password",
            placeholder="xxxx xxxx xxxx xxxx",
            help="Não é a senha normal. Gere em: Conta Google → Segurança → Verificação em duas etapas → Senhas de app.",
        )

        st.markdown("""
        <div style="background:#eaf4fb;border-left:3px solid #2e86c1;padding:8px 14px;
                    border-radius:4px;font-size:0.82rem;color:#1a5276;margin-top:4px;">
            💡 <strong>Como gerar a Senha de App do Gmail:</strong>
            acesse <em>myaccount.google.com → Segurança → Verificação em duas etapas → Senhas de app</em>.
            Crie um app chamado "Monitor Legislativo" e cole a senha de 16 caracteres aqui.
        </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Seção 2: WhatsApp (CallMeBot) ─────────────────────────────────────
        st.markdown("""
        <div style="background:#1a5276;color:white;padding:10px 18px;border-radius:8px 8px 0 0;
                    font-weight:bold;font-size:1rem;">
            📱 Alertas por WhatsApp — CallMeBot
        </div>
        <div style="background:#f4f6f8;border:1px solid #d5d8dc;border-top:none;
                    border-radius:0 0 8px 8px;padding:18px 22px;margin-bottom:18px;">
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="callmebot-instructions">
            <h4>⚠️ Ative o CallMeBot antes de usar — faça isso uma única vez:</h4>
            <ol>
                <li>Salve o número <code>+34 644 59 21 64</code> na sua agenda com o nome <strong>CallMeBot</strong>.</li>
                <li>Abra o WhatsApp e envie a mensagem exata para este contato:<br>
                    <code>I allow callmebot to send me messages</code></li>
                <li>Em segundos você receberá uma resposta com sua <strong>API Key</strong> (ex: <code>1234567</code>).</li>
                <li>Cole a API Key no campo abaixo e salve as configurações.</li>
            </ol>
            <div style="margin-top:8px;font-size:0.82rem;color:#7d6608;">
                ⏱️ Se não receber em 1 minuto, aguarde 24h e tente novamente (limite de ativações por dia).
                Serviço gratuito oferecido por <strong>callmebot.com</strong>.
            </div>
        </div>
        """, unsafe_allow_html=True)

        col3, col4 = st.columns(2)
        with col3:
            celular_whatsapp = st.text_input(
                "📞 Celular com DDD",
                value=config.get("celular_whatsapp", ""),
                placeholder="ex: 61999999999",
                help="DDD + número, sem espaços ou traços. O código do país (55) é adicionado automaticamente.",
            )
        with col4:
            callmebot_apikey = st.text_input(
                "🔑 API Key do CallMeBot",
                value=config.get("callmebot_apikey", ""),
                placeholder="ex: 1234567",
                help="Recebida via WhatsApp após a ativação.",
            )

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # ── Seção 3: Briefing automático ──────────────────────────────────────
        st.markdown("""
        <div style="background:#1a5276;color:white;padding:10px 18px;border-radius:8px 8px 0 0;
                    font-weight:bold;font-size:1rem;">
            🕐 Horário do Briefing Diário
        </div>
        <div style="background:#f4f6f8;border:1px solid #d5d8dc;border-top:none;
                    border-radius:0 0 8px 8px;padding:18px 22px;margin-bottom:18px;">
        """, unsafe_allow_html=True)

        horario_str = config.get("horario_briefing", "07:00")
        try:
            horario_default = datetime.strptime(horario_str, "%H:%M").time()
        except ValueError:
            horario_default = datetime.strptime("07:00", "%H:%M").time()

        horario_briefing = st.time_input(
            "Horário preferido para receber o briefing",
            value=horario_default,
            help="Referência de horário para envio manual ou futuras automações.",
        )

        st.markdown("""
        <div style="background:#eaf4fb;border-left:3px solid #2e86c1;padding:8px 14px;
                    border-radius:4px;font-size:0.82rem;color:#1a5276;">
            ℹ️ O envio automático agendado pode ser configurado via agendador do sistema operacional
            (ex: Agendador de Tarefas do Windows) apontando para o script de envio.
        </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Botão salvar ──────────────────────────────────────────────────────
        salvar = st.form_submit_button("💾 Salvar Configurações", use_container_width=True)

        if salvar:
            nova_config = {
                "email_destino": email_destino.strip(),
                "email_remetente": email_remetente.strip(),
                "email_senha_app": email_senha_app,
                "celular_whatsapp": celular_whatsapp.strip(),
                "callmebot_apikey": callmebot_apikey.strip(),
                "horario_briefing": horario_briefing.strftime("%H:%M"),
            }
            config_manager.salvar_config(nova_config)
            st.success("✅ Configurações salvas com sucesso!")
            st.rerun()

    # ── Teste de envio ────────────────────────────────────────────────────────
    st.markdown("<hr class='divisor-dourado'>", unsafe_allow_html=True)
    st.markdown("#### 🧪 Testar envios")

    config_atual = config_manager.carregar_config()
    col_t1, col_t2 = st.columns(2)

    with col_t1:
        if st.button("📧 Testar e-mail agora", use_container_width=True):
            if not config_atual.get("email_remetente") or not config_atual.get("email_senha_app"):
                st.error("Preencha e salve o e-mail remetente e a Senha de App primeiro.")
            elif not config_atual.get("email_destino"):
                st.error("Preencha e salve o e-mail de destino primeiro.")
            else:
                materias = storage.carregar_materias()
                if not materias:
                    st.warning("Nenhuma matéria cadastrada para incluir no teste.")
                else:
                    with st.spinner("Enviando e-mail de teste…"):
                        dados_materias = _coletar_dados_materias(materias)
                        ok, msg = notifications.enviar_email(
                            remetente=config_atual["email_remetente"],
                            senha_app=config_atual["email_senha_app"],
                            destinatario=config_atual["email_destino"],
                            assunto=f"[TESTE] Monitor Legislativo GC — {date.today().strftime('%d/%m/%Y')}",
                            materias_com_dados=dados_materias,
                        )
                    if ok:
                        st.success(f"✅ {msg} Verifique a caixa de entrada de {config_atual['email_destino']}.")
                    else:
                        st.error(f"❌ {msg}")

    with col_t2:
        if st.button("📱 Testar WhatsApp agora", use_container_width=True):
            if not config_atual.get("celular_whatsapp") or not config_atual.get("callmebot_apikey"):
                st.error("Preencha e salve o celular e a API Key do CallMeBot primeiro.")
            else:
                materias = storage.carregar_materias()
                if not materias:
                    st.warning("Nenhuma matéria cadastrada para incluir no teste.")
                else:
                    with st.spinner("Enviando mensagem de teste via WhatsApp…"):
                        dados_materias = _coletar_dados_materias(materias)
                        ok, msg = notifications.enviar_whatsapp(
                            celular=config_atual["celular_whatsapp"],
                            apikey=config_atual["callmebot_apikey"],
                            materias_com_dados=dados_materias,
                        )
                    if ok:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")
