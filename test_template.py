"""
Script de teste para verificar se o template está sendo encontrado
Execute: python test_template.py
"""
from flask import Flask, render_template
import os

app = Flask(__name__, template_folder='templates')

@app.route('/')
def test():
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'prelander.html')
        exists = os.path.exists(template_path)
        print(f"Template path: {template_path}")
        print(f"Template exists: {exists}")
        
        if exists:
            return render_template('prelander.html')
        else:
            return f"Template não encontrado em: {template_path}"
    except Exception as e:
        return f"Erro: {e}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)

