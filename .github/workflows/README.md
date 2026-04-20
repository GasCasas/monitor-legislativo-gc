# GitHub Actions — Monitor Legislativo GC

## Workflow: Alertas Legislativos (`alertas.yml`)

Verifica automaticamente mudanças de situação nas matérias monitoradas e envia
alertas por **e-mail** e **WhatsApp** quando detecta alterações.

### Horários de execução

| Horário BRT | Cron (UTC) | Dias |
|:-----------:|:----------:|:----:|
| 08:00       | `0 11 * * 1-5` | Seg–Sex |
| 13:00       | `0 16 * * 1-5` | Seg–Sex |
| 18:00       | `0 21 * * 1-5` | Seg–Sex |

O workflow também pode ser disparado manualmente em:
**GitHub → Repositório → Actions → Alertas Legislativos → Run workflow**

---

## 1. Configurar os GitHub Secrets

Acesse: **GitHub → Repositório → Settings → Secrets and variables → Actions → New repository secret**

| Secret | Descrição | Exemplo |
|--------|-----------|---------|
| `SUPABASE_URL` | URL do projeto Supabase | `https://xxxx.supabase.co` |
| `SUPABASE_SECRET_KEY` | Chave secreta do Supabase | `sb_secret_...` |
| `EMAIL_REMETENTE` | Conta Gmail que envia os alertas | `seugmail@gmail.com` |
| `EMAIL_SENHA_APP` | Senha de App do Gmail (16 chars) | `xxxx xxxx xxxx xxxx` |
| `EMAIL_DESTINO` | E-mail que recebe os alertas | `destino@exemplo.com` |
| `CELULAR_WHATSAPP` | Celular com DDD, sem espaços | `61999999999` |
| `CALLMEBOT_APIKEY` | API Key recebida via WhatsApp | `1234567` |

> **Nota:** `EMAIL_*`, `CELULAR_WHATSAPP` e `CALLMEBOT_APIKEY` são opcionais se
> já estiverem salvos na tabela `configuracoes` do Supabase via página de
> Configurações do app. O script usa env vars com prioridade e, se ausentes,
> lê do banco automaticamente.

---

## 2. Preparar o banco Supabase

O script precisa de duas colunas extras na tabela `materias` para rastrear
mudanças de situação. Execute este SQL no **Supabase → SQL Editor**:

```sql
ALTER TABLE materias
  ADD COLUMN IF NOT EXISTS situacao TEXT,
  ADD COLUMN IF NOT EXISTS situacao_verificada_em TIMESTAMPTZ;
```

Sem essas colunas, o script ainda funciona — ele detecta a ausência, registra
um aviso nos logs e não salva o histórico, mas ainda envia notificações.

---

## 3. Como gerar a Senha de App do Gmail

1. Acesse [myaccount.google.com](https://myaccount.google.com)
2. **Segurança → Verificação em duas etapas** (precisa estar ativa)
3. **Senhas de app → Criar**
4. Nome: `Monitor Legislativo GC`
5. Copie a senha gerada (16 caracteres) e cole no secret `EMAIL_SENHA_APP`

---

## 4. Como ativar o CallMeBot (WhatsApp)

1. Salve o número **+34 644 59 21 64** na sua agenda
2. Envie via WhatsApp exatamente: `I allow callmebot to send me messages`
3. Você receberá sua API Key em segundos
4. Cole a chave no secret `CALLMEBOT_APIKEY`

---

## 5. Verificar execuções

Acesse: **GitHub → Repositório → Actions → Alertas Legislativos**

Cada execução mostra:
- Matérias verificadas e resultado de cada uma
- Se houve mudanças e se as notificações foram enviadas
- Resumo final: `X matérias verificadas, Y com mudanças, Z erros`

---

## Estrutura dos arquivos

```
.github/
└── workflows/
    ├── alertas.yml     ← Definição do workflow
    └── README.md       ← Este arquivo

scripts/
└── verificar_alertas.py  ← Script de verificação (standalone)
```
