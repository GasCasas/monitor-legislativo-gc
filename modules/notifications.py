import smtplib
import requests
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ─── E-mail via Gmail SMTP ─────────────────────────────────────────────────────

def _formatar_corpo_email(materias_com_dados: list) -> str:
    data_fmt = date.today().strftime("%d/%m/%Y")
    linhas = []
    for item in materias_com_dados:
        mat = item["materia"]
        dados = item["dados"]
        casa_label = "Senado Federal" if mat["casa"] == "senado" else "Câmara dos Deputados"
        identificacao = f"{mat['tipo']} {mat['numero']}/{mat['ano']} — {casa_label}"
        ementa = dados.get("ementa", "Ementa não disponível.")
        situacao = dados.get("situacao", "Situação não disponível.")
        link = dados.get("link", "")
        obs = mat.get("observacao", "")

        bloco = f"""
        <tr>
          <td style="padding:14px 16px;border-bottom:1px solid #e8e8e8;">
            <div style="font-weight:bold;color:#1a5276;font-size:14px;">{identificacao}</div>
            <div style="color:#333;font-size:13px;margin:4px 0;">{ementa}</div>
            <div style="color:#555;font-size:12px;">🔹 <strong>Situação:</strong> {situacao}</div>
            {"<div style='color:#888;font-size:12px;font-style:italic;margin-top:2px;'>📝 " + obs + "</div>" if obs else ""}
            {"<div style='margin-top:6px;'><a href='" + link + "' style='color:#1a5276;font-size:12px;'>🔗 Ver no site oficial</a></div>" if link else ""}
          </td>
        </tr>"""
        linhas.append(bloco)

    corpo = f"""
    <html><body style="margin:0;padding:0;background:#f0f3f4;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f3f4;padding:20px 0;">
        <tr><td align="center">
          <table width="620" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

            <!-- Header -->
            <tr>
              <td style="background:linear-gradient(90deg,#1a5276,#154360);padding:22px 24px;border-left:6px solid #d4ac0d;">
                <div style="color:#d4ac0d;font-size:11px;letter-spacing:1px;text-transform:uppercase;">Gabinete do Senador</div>
                <div style="color:#ffffff;font-size:20px;font-weight:bold;margin:4px 0;">Davi Alcolumbre</div>
                <div style="color:#aac4d8;font-size:13px;">Monitor Legislativo GC — Alerta de Matérias</div>
                <div style="color:#aac4d8;font-size:12px;margin-top:6px;">📅 {data_fmt}</div>
              </td>
            </tr>

            <!-- Matérias -->
            <tr><td style="padding:16px 16px 4px 16px;font-size:13px;color:#555;">
              Abaixo o status atualizado das <strong>{len(materias_com_dados)}</strong> matéria(s) monitoradas:
            </td></tr>
            <tr><td>
              <table width="100%" cellpadding="0" cellspacing="0">
                {"".join(linhas)}
              </table>
            </td></tr>

            <!-- Footer -->
            <tr>
              <td style="background:#f4f6f8;padding:14px 24px;font-size:11px;color:#888;text-align:center;">
                Monitor Legislativo GC • Senado Federal &amp; Câmara dos Deputados<br>
                APIs Abertas — Dados Públicos
              </td>
            </tr>

          </table>
        </td></tr>
      </table>
    </body></html>
    """
    return corpo


def enviar_email(
    remetente: str,
    senha_app: str,
    destinatario: str,
    assunto: str,
    materias_com_dados: list,
) -> tuple:
    """Envia e-mail HTML via Gmail SMTP com o resumo das matérias."""
    try:
        corpo_html = _formatar_corpo_email(materias_com_dados)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = f"Monitor Legislativo GC <{remetente}>"
        msg["To"] = destinatario
        msg.attach(MIMEText(corpo_html, "html", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(remetente, senha_app)
            smtp.sendmail(remetente, destinatario, msg.as_string())

        return True, "E-mail enviado com sucesso!"
    except smtplib.SMTPAuthenticationError:
        return False, (
            "Erro de autenticação no Gmail. Verifique o e-mail remetente e a "
            "Senha de App (não é a senha normal da conta)."
        )
    except smtplib.SMTPException as e:
        return False, f"Erro SMTP: {e}"
    except Exception as e:
        return False, f"Erro inesperado: {e}"


# ─── WhatsApp via CallMeBot ────────────────────────────────────────────────────

def _normalizar_celular(celular: str) -> str:
    """Garante que o número tenha o código do país 55 (Brasil)."""
    numero = "".join(filter(str.isdigit, celular))
    if len(numero) == 11 and not numero.startswith("55"):
        numero = "55" + numero
    elif len(numero) == 10 and not numero.startswith("55"):
        numero = "55" + numero
    return numero


def _formatar_mensagem_whatsapp(materias_com_dados: list) -> str:
    data_fmt = date.today().strftime("%d/%m/%Y")
    linhas = [f"📋 *Monitor Legislativo GC — {data_fmt}*", ""]
    for item in materias_com_dados:
        mat = item["materia"]
        dados = item["dados"]
        casa_label = "Senado" if mat["casa"] == "senado" else "Câmara"
        identificacao = f"{mat['tipo']} {mat['numero']}/{mat['ano']} ({casa_label})"
        situacao = dados.get("situacao", "Situação não disponível.")
        linhas.append(f"🔹 *{identificacao}*")
        linhas.append(f"   {situacao}")
        if mat.get("observacao"):
            linhas.append(f"   _{mat['observacao']}_")
        linhas.append("")
    linhas.append("_Enviado pelo Monitor Legislativo GC_")
    return "\n".join(linhas)


def enviar_whatsapp(celular: str, apikey: str, materias_com_dados: list) -> tuple:
    """Envia mensagem via CallMeBot WhatsApp API."""
    numero = _normalizar_celular(celular)
    mensagem = _formatar_mensagem_whatsapp(materias_com_dados)

    try:
        r = requests.get(
            "https://api.callmebot.com/whatsapp.php",
            params={"phone": numero, "text": mensagem, "apikey": apikey},
            timeout=20,
        )
        texto = r.text.strip()
        if r.status_code == 200 and ("Message Sent" in texto or "queued" in texto.lower()):
            return True, "Mensagem WhatsApp enviada com sucesso!"
        return False, f"Resposta da API CallMeBot: {texto[:300]}"
    except requests.exceptions.Timeout:
        return False, "Tempo de conexão esgotado com a API CallMeBot."
    except Exception as e:
        return False, f"Erro ao enviar WhatsApp: {e}"
