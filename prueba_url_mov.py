from flask import Flask, redirect, request, render_template_string
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import os
from dotenv import load_dotenv
import socket

# Cargar variables del .env
load_dotenv()

# Configurar Flask
app = Flask(__name__)

# Obtener IP local
def obtener_ip_local():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

ip_local = obtener_ip_local()

# Instancia global de SpotifyOAuth (usa archivo de cache por usuario)
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope=os.getenv("SPOTIPY_SCOPE"),
    cache_path=".spotify_token_cache"
)

# Plantilla HTML simple
HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
    <title>Iniciar sesión en Spotify</title>
</head>
<body>
    <h1>Iniciar sesión en Spotify</h1>
    <a href="/login"><button>Iniciar sesión</button></a>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_LOGIN)

@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)

    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])
        user = sp.current_user()
        return f"<h1>¡Hola {user['display_name']}!</h1><p>Sesión iniciada correctamente.</p>"
    else:
        return "Error al iniciar sesión.", 400

if __name__ == "__main__":
    print(f"Servidor corriendo en http://{ip_local}:5000")
    app.run(host='0.0.0.0', port=5000)
