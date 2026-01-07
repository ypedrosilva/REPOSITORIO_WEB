"""
Servidor web com pre-lander que captura dados do Facebook Ads e redireciona para o bot do Telegram
Usa PostgreSQL para armazenar dados dos cliques
"""
from flask import Flask, request, render_template, jsonify
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

# Configuração do PostgreSQL
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
                screen_width TEXT,
                screen_height TEXT,
                language TEXT,
                timezone TEXT,
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

def save_click_data(click_id, fbclid, useragent, ip, fbb, sub1, sub2, sub3, sub4, sub5, screen_width=None, screen_height=None, language=None, timezone=None):
    """Salva dados do clique no banco"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO clicks 
            (click_id, fbclid, useragent, ip, fbb, sub1, sub2, sub3, sub4, sub5, screen_width, screen_height, language, timezone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (click_id, fbclid, useragent, ip, fbb, sub1, sub2, sub3, sub4, sub5, screen_width, screen_height, language, timezone))
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
def prelander():
    """Exibe a pre-lander"""
    return render_template('prelander.html')

@app.route('/save-click', methods=['POST'])
def save_click():
    """Endpoint que recebe dados do JavaScript e salva no banco"""
    
    if not BOT_USERNAME:
        return jsonify({"success": False, "error": "BOT_USERNAME não configurado"}), 500
    
    if not DATABASE_URL:
        return jsonify({"success": False, "error": "DATABASE_URL não configurado"}), 500
    
    try:
        # Receber dados do JavaScript
        data = request.get_json()
        
        # Gerar ID único para este clique
        click_id = str(uuid.uuid4()).replace('-', '')[:12]
        
        # Extrair dados
        fbclid = data.get('fbclid', '')
        fbb = data.get('fbb', '')
        useragent = data.get('useragent', '')
        ip = data.get('ip', get_client_ip())
        sub1 = data.get('sub1', '')
        sub2 = data.get('sub2', '')
        sub3 = data.get('sub3', '')
        sub4 = data.get('sub4', '')
        sub5 = data.get('sub5', '')
        screen_width = data.get('screen_width', '')
        screen_height = data.get('screen_height', '')
        language = data.get('language', '')
        timezone = data.get('timezone', '')
        
        # Salvar dados do clique no banco
        success = save_click_data(
            click_id, fbclid, useragent, ip, fbb, 
            sub1, sub2, sub3, sub4, sub5,
            screen_width, screen_height, language, timezone
        )
        
        if success:
            logger.info(f"Clique {click_id} salvo - Redirecionando para Telegram")
            return jsonify({
                "success": True,
                "click_id": click_id,
                "bot_username": BOT_USERNAME
            })
        else:
            return jsonify({"success": False, "error": "Erro ao salvar no banco"}), 500
            
    except Exception as e:
        logger.error(f"Erro ao processar clique: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/health')
def health():
    """Endpoint de health check"""
    return jsonify({
        "status": "ok", 
        "bot_username": BOT_USERNAME, 
        "database": "connected" if DATABASE_URL else "not configured"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)
