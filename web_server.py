"""
Servidor web que captura dados do Facebook Ads e redireciona para o bot do Telegram
Usa PostgreSQL para armazenar dados dos cliques
"""
from flask import Flask, request, redirect
import os
import logging
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Configurações
BOT_USERNAME = os.getenv('BOT_USERNAME', '')
PORT = int(os.getenv('PORT', 5000))

# Configuração do PostgreSQL (Railway fornece automaticamente)
DATABASE_URL = os.getenv('DATABASE_URL', '')

def get_db_connection():
    """Conecta ao banco PostgreSQL"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {e}")
        return None

def init_database():
    """Cria as tabelas se não existirem"""
    conn = get_db_connection()
    if not conn:
        logger.error("Não foi possível conectar ao banco para inicializar")
        return
    
    try:
        cursor = conn.cursor()
        # Tabela de cliques
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clicks (
                click_id VARCHAR(12) PRIMARY KEY,
                fbclid TEXT,
                useragent TEXT,
                ip TEXT,
                fbb TEXT,
                sub1 TEXT,
                sub2 TEXT,
                sub3 TEXT,
                sub4 TEXT,
                sub5 TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used BOOLEAN DEFAULT FALSE
            )
        ''')
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                fbclid TEXT,
                useragent TEXT,
                ip TEXT,
                fbb TEXT,
                sub1 TEXT,
                sub2 TEXT,
                sub3 TEXT,
                sub4 TEXT,
                sub5 TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logger.info("Banco de dados inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco: {e}")
    finally:
        conn.close()

def save_click_data(click_id, fbclid, useragent, ip, fbb, sub1, sub2, sub3, sub4, sub5):
    """Salva dados do clique no banco"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO clicks 
            (click_id, fbclid, useragent, ip, fbb, sub1, sub2, sub3, sub4, sub5)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (click_id, fbclid, useragent, ip, fbb, sub1, sub2, sub3, sub4, sub5))
        conn.commit()
        logger.info(f"Clique {click_id} salvo no banco")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar clique: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_client_ip():
    """Obtém o IP real do cliente"""
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr
    return ip

# Inicializar banco ao iniciar
if DATABASE_URL:
    init_database()
else:
    logger.warning("DATABASE_URL não configurado!")

@app.route('/')
def redirect_to_bot():
    """Endpoint principal que captura dados e redireciona para o bot"""
    
    if not BOT_USERNAME:
        return "❌ BOT_USERNAME não configurado!", 500
    
    if not DATABASE_URL:
        return "❌ DATABASE_URL não configurado!", 500
    
    # Gerar ID único para este clique
    click_id = str(uuid.uuid4()).replace('-', '')[:12]
    
    # Capturar parâmetros da URL
    fbclid = request.args.get('fbclid', '')
    fbb = request.args.get('fbb', '')
    sub1 = request.args.get('sub1', '')
    sub2 = request.args.get('sub2', '')
    sub3 = request.args.get('sub3', '')
    sub4 = request.args.get('sub4', '')
    sub5 = request.args.get('sub5', '')
    
    # Capturar dados do request
    user_agent = request.headers.get('User-Agent', '')
    client_ip = get_client_ip()
    
    # Salvar dados do clique no banco
    save_click_data(click_id, fbclid, user_agent, client_ip, fbb, sub1, sub2, sub3, sub4, sub5)
    
    # Redirecionar para o bot com apenas o ID
    telegram_url = f"https://t.me/{BOT_USERNAME}?start={click_id}"
    
    logger.info(f"Clique {click_id} - Redirecionando para Telegram")
    
    return redirect(telegram_url, code=302)

@app.route('/health')
def health():
    """Endpoint de health check"""
    return {"status": "ok", "bot_username": BOT_USERNAME, "database": "connected" if DATABASE_URL else "not configured"}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)

