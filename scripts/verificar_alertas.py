#!/usr/bin/env python3
"""
verificar_alertas.py
──────────────────────────────────────────────────────────────────────────────
Verifica mudanças de situação nas matérias monitoradas e envia alertas por
WhatsApp (CallMeBot) e e-mail (Gmail SMTP).

Executado automaticamente pelo GitHub Actions (seg-sex 08h/13h/18h BRT)
ou manualmente via: python scripts/verificar_alertas.py

Variáveis de ambiente necessárias (GitHub Secrets):
  SUPABASE_URL          — URL do projeto Supabase
  SUPABASE_SECRET_KEY   — Chave secreta do Supabase
  EMAIL_REMETENTE       — Conta Gmail remetente
  EMAIL_SENHA_APP       — Senha de App do Gmail (não a senha normal)
  EMAIL_DESTINO         — E-mail que receberá os alertas
  CELULAR_WHATSAPP      — Celular com DDD (ex: 61999999999)
  CALLMEBOT_APIKEY      — API Key do CallMeBot

Obs: se EMAIL_* / CELULAR_* / CALLMEBOT_* não forem definidos como env vars,
o script os lê automaticamente da tabela `configuracoes` do Supabase.
"""

from __future__ import annotations

import os
import sys
import smtplib
import requests
from datetime import date, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Credenciais Supabase (obrigatórias) ───────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_SECRET_KEY", "").strip()

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERRO: SUPABASE_URL e SUPABASE_SECRET_KEY são obrigatórios.")
    sys.exit(1)

# ── Cliente Supabase ──────────────────────────────────────────────────────────
try:
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"ERRO ao conectar ao Supabase: {e}")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# CREDENCIAIS DE NOTIFICAÇÃO
# Prioridade: env var → tabela configuracoes do Supabase
# ══════════════════════════════════════════════════════════════════════════════

def _carregar_config_notificacao() -> dict:
    config = {
        "email_remetente":  os.environ.get("EMAIL_REMETENTE", "").strip(),
        "email_senha_app":  os.environ.get("EMAIL_SENHA_APP", "").strip(),
        "email_destino":    os.environ.get("EMAIL_DESTINO", "").strip(),
        "celular_whatsapp": os.environ.get("CELULAR_WHATSAPP", "").strip(),
        "callmebot_apikey": os.environ.get("CALLMEBOT_APIKEY", "").strip(),
    }
    # Preenche campos ausentes com valores do Supabase configuracoes
    campos_faltando = [k for k, v in config.items() if not v]
    if campos_faltando:
        try:
            res = sb.table("configuracoes").select("chave, valor").execute()
            for row in (res.data or []):
                if row["chave"] in campos_faltando and row["valor"]:
                    config[row["chave"]] = row["valor"]
        except Exception:
            pass
    return config


# ══════════════════════════════════════════════════════════════════════════════
# CONSULTAS ÀS APIs LEGISLATIVAS
# ══════════════════════════════════════════════════════════════════════════════

_HEADERS = {"Accept": "application/json"}
_TIMEOUT = 15


def _get(url: str, params: dict = None) -> dict | None:
    try:
        r = requests.get(url, headers=_HEADERS, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _situacao_senado(tipo: str, numero: str, ano: str) -> dict:
    """Retorna ementa e situação atual de uma matéria do Senado."""
    data = _get(f"https://legis.senado.leg.br/dadosabertos/materia/{tipo}/{numero}/{ano}.json")
    if not data:
        return {}
    try:
        materia = data["DetalheMateria"]["Materia"]
        ementa = materia.get("DadosBasicosMateria", {}).get("EmentaMateria", "")
        codigo = materia.get("IdentificacaoMateria", {}).get("CodigoMateria", "")
        link   = f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{codigo}" if codigo else ""

        situacao_txt = ""
        if codigo:
            sit = _get(f"https://legis.senado.leg.br/dadosabertos/materia/situacaoatual/{codigo}.json")
            if sit:
                mat_sit = sit.get("SituacaoAtualMateria", {}).get("Materias", {}).get("Materia", {})
                if isinstance(mat_sit, list):
                    mat_sit = mat_sit[0] if mat_sit else {}
                aut = (
                    mat_sit.get("SituacaoAtual", {})
                    .get("Autuacoes", {})
                    .get("Autuacao", {})
                )
                if isinstance(aut, list):
                    aut = aut[-1] if aut else {}
                situacoes = aut.get("Situacoes", {}).get("Situacao", {})
                if isinstance(situacoes, list):
                    situacoes = situacoes[-1] if situacoes else {}
                descricao   = situacoes.get("DescricaoSituacao", "")
                data_sit    = situacoes.get("DataSituacao", "")
                local_nome  = aut.get("NomeLocal", "")
                sigla_local = aut.get("SiglaLocal", "")
                local_str   = f"{local_nome} ({sigla_local})" if local_nome and sigla_local else local_nome
                partes = [p for p in [descricao, local_str] if p]
                if data_sit:
                    try:
                        partes.append(f"em {datetime.strptime(data_sit, '%Y-%m-%d').strftime('%d/%m/%Y')}")
                    except ValueError:
                        pass
                situacao_txt = " — ".join(partes)

        return {"ementa": ementa, "situacao": situacao_txt, "link": link}
    except (KeyError, TypeError):
        return {}


def _situacao_camara(tipo: str, numero: str, ano: str) -> dict:
    """Retorna ementa e situação atual de uma proposição da Câmara."""
    data = _get(
        "https://dadosabertos.camara.leg.br/api/v2/proposicoes",
        params={"siglaTipo": tipo, "numero": numero, "ano": ano, "itens": 1},
    )
    if not data or not data.get("dados"):
        return {}
    try:
        prop_id = data["dados"][0]["id"]
        detalhe = _get(f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{prop_id}")
        if not detalhe or not detalhe.get("dados"):
            return {}
        d = detalhe["dados"]
        ementa  = d.get("ementa", "")
        status  = d.get("statusProposicao", {})
        descr   = status.get("descricaoSituacao", "")
        orgao   = status.get("siglaOrgao", "")
        situacao_txt = f"{descr} — {orgao}" if orgao else descr
        link = f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={prop_id}"
        return {"ementa": ementa, "situacao": situacao_txt, "link": link}
    except (KeyError, TypeError, IndexError):
        return {}


def buscar_situacao(mat: dict) -> dict:
    if mat.get("casa") == "senado":
        return _situacao_senado(mat["tipo"], mat["numero"], mat["ano"])
    return _situacao_camara(mat["tipo"], mat["numero"], mat["ano"])


# ══════════════════════════════════════════════════════════════════════════════
# PERSISTÊNCIA — atualiza situação no Supabase
# ══════════════════════════════════════════════════════════════════════════════

def _atualizar_situacao_no_banco(materia_id: str, dados_api: dict) -> bool:
    """Persiste situação, ementa e link retornados pela API no Supabase."""
    try:
        sb.table("materias").update({
            "situacao":           dados_api.get("situacao", ""),
            "ementa":             dados_api.get("ementa", ""),
            "link":               dados_api.get("link", ""),
            "ultima_verificacao": datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC"),
            "status":             "ok",
        }).eq("id", materia_id).execute()
        return True
    except Exception as e:
        print(f"  ⚠️  Erro ao salvar no banco: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# NOTIFICAÇÕES
# ══════════════════════════════════════════════════════════════════════════════

def _enviar_email(cfg: dict, mudancas: list) -> bool:
    if not cfg.get("email_remetente") or not cfg.get("email_senha_app") or not cfg.get("email_destino"):
        print("  ⚠️  E-mail não configurado — pulando.")
        return False

    data_fmt = date.today().strftime("%d/%m/%Y")
    linhas_html = ""
    for item in mudancas:
        mat  = item["materia"]
        casa = "Senado" if mat.get("casa") == "senado" else "Câmara"
        link = item["api"].get("link", "")
        link_tag = f'<a href="{link}" style="color:#1a5276;">🔗 ver</a>' if link else ""
        linhas_html += f"""
        <tr>
          <td style="padding:12px 16px;border-bottom:1px solid #e8e8e8;">
            <div style="font-weight:bold;color:#1a5276;">
              {mat['tipo']} {mat['numero']}/{mat['ano']} — {casa}
              {"&nbsp;" + link_tag if link_tag else ""}
            </div>
            <div style="font-size:12px;color:#c0392b;margin:3px 0;">
              <strong>Anterior:</strong> {item['situacao_anterior'] or '(sem registro)'}
            </div>
            <div style="font-size:12px;color:#196f3d;">
              <strong>Nova:</strong> {item['situacao_nova']}
            </div>
            {"<div style='font-size:11px;color:#888;font-style:italic;margin-top:3px;'>"+mat['observacao']+"</div>" if mat.get('observacao') else ""}
          </td>
        </tr>"""

    corpo = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f0f3f4;">
    <table width="100%" style="padding:20px 0;"><tr><td align="center">
    <table width="600" style="background:#fff;border-radius:10px;overflow:hidden;">
      <tr><td style="background:linear-gradient(90deg,#1a5276,#154360);padding:18px 24px;border-left:6px solid #d4ac0d;">
        <div style="color:#d4ac0d;font-size:11px;letter-spacing:1px;">ALERTA LEGISLATIVO</div>
        <div style="color:#fff;font-size:18px;font-weight:bold;">Monitor Legislativo GC</div>
        <div style="color:#aac4d8;font-size:12px;">Gabinete do Senador Davi Alcolumbre — {data_fmt}</div>
      </td></tr>
      <tr><td style="padding:14px 16px;font-size:13px;color:#555;">
        <strong>{len(mudancas)}</strong> matéria(s) com mudança de situação detectada(s):
      </td></tr>
      <tr><td><table width="100%">{linhas_html}</table></td></tr>
      <tr><td style="background:#f4f6f8;padding:12px 24px;font-size:11px;color:#888;text-align:center;">
        Monitor Legislativo GC • Alerta automático gerado às {datetime.now().strftime('%H:%M')}
      </td></tr>
    </table></td></tr></table>
    </body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"⚠️ Alerta Legislativo — {len(mudancas)} mudança(s) — {data_fmt}"
        msg["From"]    = f"Monitor Legislativo GC <{cfg['email_remetente']}>"
        msg["To"]      = cfg["email_destino"]
        msg.attach(MIMEText(corpo, "html", "utf-8"))
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo(); smtp.starttls()
            smtp.login(cfg["email_remetente"], cfg["email_senha_app"])
            smtp.sendmail(cfg["email_remetente"], cfg["email_destino"], msg.as_string())
        print(f"  ✅ E-mail enviado para {cfg['email_destino']}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("  ❌ Erro de autenticação Gmail. Verifique a Senha de App.")
        return False
    except Exception as e:
        print(f"  ❌ Erro ao enviar e-mail: {e}")
        return False


def _enviar_whatsapp(cfg: dict, mudancas: list) -> bool:
    if not cfg.get("celular_whatsapp") or not cfg.get("callmebot_apikey"):
        print("  ⚠️  WhatsApp não configurado — pulando.")
        return False

    data_fmt = date.today().strftime("%d/%m/%Y")
    linhas = [f"⚠️ *Alerta Legislativo — {data_fmt}*", f"*{len(mudancas)} mudança(s) detectada(s):*", ""]
    for item in mudancas:
        mat  = item["materia"]
        casa = "Senado" if mat.get("casa") == "senado" else "Câmara"
        linhas.append(f"🔹 *{mat['tipo']} {mat['numero']}/{mat['ano']} ({casa})*")
        linhas.append(f"   Antes: _{item['situacao_anterior'] or 'sem registro'}_")
        linhas.append(f"   Agora: _{item['situacao_nova']}_")
        if mat.get("observacao"):
            linhas.append(f"   {mat['observacao']}")
        linhas.append("")
    linhas.append("_Monitor Legislativo GC — Gabinete Davi Alcolumbre_")
    mensagem = "\n".join(linhas)

    numero = "".join(filter(str.isdigit, cfg["celular_whatsapp"]))
    if len(numero) == 11 and not numero.startswith("55"):
        numero = "55" + numero

    try:
        r = requests.get(
            "https://api.callmebot.com/whatsapp.php",
            params={"phone": numero, "text": mensagem, "apikey": cfg["callmebot_apikey"]},
            timeout=20,
        )
        texto = r.text.strip()
        if r.status_code == 200 and ("Message Sent" in texto or "queued" in texto.lower()):
            print(f"  ✅ WhatsApp enviado para {cfg['celular_whatsapp']}")
            return True
        print(f"  ❌ CallMeBot retornou: {texto[:200]}")
        return False
    except Exception as e:
        print(f"  ❌ Erro WhatsApp: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# EXECUÇÃO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    inicio = datetime.now()
    print("=" * 60)
    print(f"Monitor Legislativo GC — Verificação de Alertas")
    print(f"Início: {inicio.strftime('%d/%m/%Y %H:%M:%S')} (UTC)")
    print("=" * 60)

    # 1. Carrega matérias do Supabase
    try:
        res = sb.table("materias").select("*").order("criado_em").execute()
        materias = res.data or []
    except Exception as e:
        print(f"ERRO ao carregar matérias: {e}")
        sys.exit(1)

    if not materias:
        print("Nenhuma matéria cadastrada. Nada a verificar.")
        print(f"\nResumo: 0 matérias verificadas, 0 com mudanças.")
        return

    print(f"\n{len(materias)} matéria(s) para verificar:\n")

    cfg_notif = _carregar_config_notificacao()
    mudancas  = []
    erros     = 0

    # 2. Verifica cada matéria
    for mat in materias:
        casa  = "Senado" if mat.get("casa") == "senado" else "Câmara"
        ident = f"{mat['tipo']} {mat['numero']}/{mat['ano']} ({casa})"
        print(f"  Verificando {ident}...")

        dados_api = buscar_situacao(mat)
        if not dados_api:
            print(f"    ⚠️  Sem resposta da API — pulando.")
            try:
                sb.table("materias").update({"status": "erro"}).eq("id", mat["id"]).execute()
            except Exception:
                pass
            erros += 1
            continue

        situacao_nova     = dados_api.get("situacao", "").strip()
        situacao_anterior = (mat.get("situacao") or "").strip()

        if not situacao_nova:
            print(f"    ⚠️  Situação não retornada pela API.")
            erros += 1
            continue

        if situacao_anterior == situacao_nova:
            print(f"    ✓  Sem mudança: {situacao_nova[:80]}{'…' if len(situacao_nova) > 80 else ''}")
            # Atualiza timestamp e ementa/link mesmo sem mudança de situação
            _atualizar_situacao_no_banco(mat["id"], dados_api)
            continue

        if not situacao_anterior:
            print(f"    📝 Primeira verificação — situação registrada.")
        else:
            print(f"    🔔 MUDANÇA DETECTADA!")
            print(f"       Anterior: {situacao_anterior[:80]}")
            print(f"       Nova:     {situacao_nova[:80]}")
            mudancas.append({
                "materia":           mat,
                "situacao_anterior": situacao_anterior,
                "situacao_nova":     situacao_nova,
                "api":               dados_api,
            })

        _atualizar_situacao_no_banco(mat["id"], dados_api)

    # 3. Envia notificações se houver mudanças
    print()
    if mudancas:
        print(f"🔔 {len(mudancas)} mudança(s) encontrada(s). Enviando notificações...\n")
        _enviar_email(cfg_notif, mudancas)
        _enviar_whatsapp(cfg_notif, mudancas)
    else:
        print("✓  Nenhuma mudança detectada. Notificações não enviadas.")

    # 4. Resumo final
    duracao = (datetime.now() - inicio).seconds
    print()
    print("=" * 60)
    print(f"Resumo: {len(materias)} matéria(s) verificada(s), "
          f"{len(mudancas)} com mudança(s), {erros} erro(s).")
    print(f"Duração: {duracao}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
