import time
import urllib.request
import json
import sqlite3
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- SERVIDOR WEB PARA O RENDER ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Star Wars MMO Rodando com Sucesso!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('game_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            name TEXT,
            classe TEXT,
            credits INTEGER,
            hp INTEGER,
            level INTEGER,
            location TEXT,
            patente TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_player(user_id):
    conn = sqlite3.connect('game_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, classe, credits, hp, level, location, patente FROM players WHERE id = ?', (user_id,))
    player = cursor.fetchone()
    conn.close()
    return player

def create_player(user_id, name, classe):
    conn = sqlite3.connect('game_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO players (id, name, classe, credits, hp, level, location, patente) VALUES (?, ?, ?, 500, 100, 1, ?, ?)', 
                   (user_id, name, classe, 'Tatooine', 'Recruta'))
    conn.commit()
    conn.close()

def update_player_resources(user_id, add_credits, add_level=0, add_hp=0):
    conn = sqlite3.connect('game_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT credits, level, hp FROM players WHERE id = ?', (user_id,))
    res = cursor.fetchone()
    if res:
        novo_cred = res[0] + add_credits
        novo_lvl = res[1] + add_level
        novo_hp = min(100, res[2] + add_hp)
        cursor.execute('UPDATE players SET credits = ?, level = ?, hp = ? WHERE id = ?', (novo_cred, novo_lvl, novo_hp, user_id))
        conn.commit()
        conn.close()

TOKEN = "8756370604:AAEuYblUJ4OOdqoy7kGl1JTk0QtE72p9bCI"
URL = f"https://api.telegram.org/bot{TOKEN}"

def enviar_mensagem(chat_id, texto):
    data = {"chat_id": chat_id, "text": texto, "parse_mode": "Markdown"}
    req = urllib.request.Request(f"{URL}/sendMessage", data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    urllib.request.urlopen(req)

def processar_updates():
    init_db()
    offset = 0
    print("Bot rodando!")
    while True:
        try:
            resposta = urllib.request.urlopen(f"{URL}/getUpdates?offset={offset}&timeout=30", timeout=35)
            dados = json.loads(resposta.read().decode('utf-8'))
            for resultado in dados.get("result", []):
                offset = resultado["update_id"] + 1
                if "message" in resultado:
                    msg = resultado["message"]
                    chat_id = msg["chat"]["id"]
                    user_id = msg["from"]["id"]
                    texto = msg.get("text", "")
                    if texto == "/start":
                        player = get_player(user_id)
                        if not player:
                            create_player(user_id, msg["from"].get("first_name", "Comandante"), "Soldado")
                            enviar_mensagem(chat_id, "Bem-vindo à Orla Exterior! Você iniciou sua jornada no RPG.")
                        else:
                            enviar_mensagem(chat_id, f"Olá novamente, {player[0]}! Você possui {player[2]} créditos.")
        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(2)

if __name__ == '__main__':
    # Inicia o servidor web em segundo plano para manter o Render ativo
    t = threading.Thread(target=run_web_server)
    t.daemon = True
    t.start()
    
    # Inicia o bot do Telegram
    processar_updates()
