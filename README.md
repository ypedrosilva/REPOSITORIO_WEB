# Servidor Web - Funil Full Track

Servidor Flask que captura dados do Facebook Ads e redireciona para o bot do Telegram.

## 📁 Arquivos deste repositório

- `web_server.py` - Servidor Flask
- `requirements.txt` - Dependências
- `Procfile` - Configuração Railway
- `runtime.txt` - Versão Python

## 🚀 Deploy no Railway

1. Conecte este repositório no Railway
2. Configure as variáveis:
   - `BOT_USERNAME` = `notorioussilvamines1bot`
   - `DATABASE_URL` = (URL do PostgreSQL)
3. Configure Start Command: `gunicorn web_server:app --bind 0.0.0.0:$PORT`
4. Gere o domínio público

## 📖 Instruções completas

Veja o arquivo `CONFIGURAR_POSTGRESQL.md` na raiz do projeto principal.

