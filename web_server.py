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

# Configurar Flask para encontrar templates
app = Flask(__name__, template_folder='templates')
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
    """Cria as tabelas se não existirem e adiciona colunas faltantes"""
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
        
        # Adicionar colunas novas se não existirem (migração)
        columns_to_add = [
            ('screen_width', 'TEXT'),
            ('screen_height', 'TEXT'),
            ('language', 'TEXT'),
            ('timezone', 'TEXT')
        ]
        
        # PostgreSQL não suporta IF NOT EXISTS em ALTER TABLE diretamente
        # Vamos verificar se a coluna existe antes de adicionar
        for column_name, column_type in columns_to_add:
            try:
                cursor.execute('''
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'clicks' AND column_name = %s
                ''', (column_name,))
                
                if not cursor.fetchone():
                    # Coluna não existe, adicionar
                    cursor.execute(f'ALTER TABLE clicks ADD COLUMN {column_name} {column_type}')
                    logger.info(f"Coluna {column_name} adicionada")
                else:
                    logger.debug(f"Coluna {column_name} já existe")
            except Exception as e:
                logger.warning(f"Erro ao verificar/adicionar coluna {column_name}: {e}")
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
        
        # Verificar quais colunas existem na tabela
        cursor.execute('''
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'clicks'
        ''')
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Construir query baseado nas colunas existentes
        base_columns = ['click_id', 'fbclid', 'useragent', 'ip', 'fbb', 'sub1', 'sub2', 'sub3', 'sub4', 'sub5']
        base_values = [click_id, fbclid, useragent, ip, fbb, sub1, sub2, sub3, sub4, sub5]
        
        # Adicionar colunas opcionais se existirem
        optional_columns = {
            'screen_width': screen_width,
            'screen_height': screen_height,
            'language': language,
            'timezone': timezone
        }
        
        for col_name, col_value in optional_columns.items():
            if col_name in existing_columns:
                base_columns.append(col_name)
                base_values.append(col_value)
        
        # Construir e executar query
        columns_str = ', '.join(base_columns)
        placeholders = ', '.join(['%s'] * len(base_columns))
        
        cursor.execute(f'''
            INSERT INTO clicks ({columns_str})
            VALUES ({placeholders})
        ''', tuple(base_values))
        
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
    logger.info("Rota / acessada - Servindo pre-lander")
    try:
        # Tentar renderizar o template
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'prelander.html')
        logger.info(f"Tentando carregar template de: {template_path}")
        
        if os.path.exists(template_path):
            logger.info("Template encontrado, renderizando...")
            return render_template('prelander.html')
        else:
            logger.warning(f"Template não encontrado em {template_path}, usando fallback")
            raise FileNotFoundError(f"Template não encontrado")
    except Exception as e:
        logger.error(f"Erro ao renderizar template: {e}")
        # Fallback: retornar HTML direto se template não for encontrado
        logger.info("Usando HTML fallback")
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Carregando...</title>
            <style>
                body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; color: white; }
                .spinner { border: 4px solid rgba(255,255,255,0.3); border-top: 4px solid white; border-radius: 50%; width: 60px; height: 60px; animation: spin 1s linear infinite; margin: 0 auto 2rem; }
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            </style>
        </head>
        <body>
            <div style="text-align: center;">
                <div class="spinner"></div>
                <h1>Preparando tudo para você...</h1>
                <p>Aguarde um momento...</p>
            </div>
            <script>
                const urlParams = new URLSearchParams(window.location.search);
                const params = {};
                urlParams.forEach((value, key) => { params[key] = value; });
                params.useragent = navigator.userAgent;
                params.screen_width = window.screen.width;
                params.screen_height = window.screen.height;
                params.language = navigator.language;
                params.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                
                async function getIP() {
                    try {
                        const response = await fetch('https://api.ipify.org?format=json');
                        const data = await response.json();
                        return data.ip;
                    } catch { return 'unknown'; }
                }
                
                async function processAndRedirect() {
                    try {
                        params.ip = await getIP();
                        const response = await fetch('/save-click', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(params)
                        });
                        const data = await response.json();
                        if (data.success && data.click_id) {
                            await new Promise(r => setTimeout(r, 500));
                            window.location.href = `https://t.me/${data.bot_username}?start=${data.click_id}`;
                        } else {
                            window.location.href = `https://t.me/notorioussilvamines1bot`;
                        }
                    } catch (error) {
                        window.location.href = `https://t.me/notorioussilvamines1bot`;
                    }
                }
                // Aguardar 2 segundos para mostrar a pre-lander
                window.addEventListener('load', () => setTimeout(processAndRedirect, 2000));
            </script>
        </body>
        </html>
        """, 200

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
