# Servidor Web - Funil Full Track

Servidor Flask com pre-lander que captura dados do Facebook Ads e redireciona para o bot do Telegram.

## 📁 Estrutura

```
REPOSITORIO_WEB/
├── web_server.py          # Servidor Flask
├── templates/
│   └── prelander.html     # Página de pre-lander
├── requirements.txt       # Dependências
├── Procfile              # Configuração Railway
├── runtime.txt           # Versão Python
└── README.md             # Este arquivo
```

## 🚀 Deploy no Railway

1. Conecte este repositório no Railway
2. Configure as variáveis:
   - `BOT_USERNAME` = `notorioussilvamines1bot`
   - `DATABASE_URL` = (URL do PostgreSQL)
3. Configure Start Command: `gunicorn web_server:app --bind 0.0.0.0:$PORT`
4. Gere o domínio público

## 📖 Instruções Completas

Veja o arquivo `GUIA_COMPLETO.md` na raiz do projeto principal.

## 🎨 Pre-lander

A pre-lander:
- Captura todos os dados do Facebook (fbclid, fbb, etc.)
- Captura dados do navegador (useragent, IP, resolução, idioma, timezone)
- Salva tudo no PostgreSQL
- Redireciona para o bot do Telegram com ID único

## ✅ Funcionalidades

- ✅ Pre-lander bonita e profissional
- ✅ Captura completa de dados
- ✅ Salvamento garantido no banco antes de redirecionar
- ✅ Redirecionamento automático para o bot
