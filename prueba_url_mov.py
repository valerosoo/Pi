import threading
import asyncio
import edge_tts
import os
import pygame
import speech_recognition as sr
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import subprocess
import time
import webbrowser
from flask import Flask, redirect, request, render_template_string
from dotenv import load_dotenv
import socket

app = Flask(__name__)

# Obtener IP local
def obtener_ip_local():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

ip_local = obtener_ip_local()

# Autenticación con Spotify
sp = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope=os.getenv("SPOTIPY_SCOPE"),
    cache_path=".spotify_token_cache"
)

# Reconocimiento de voz
async def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        pygame.mixer.init()
        pygame.mixer.music.load("audio_home.mp3")
        pygame.mixer.music.play()
        await asyncio.sleep(1)
        pygame.mixer.music.stop()
        pygame.mixer.quit()

        recognizer.pause_threshold = 1.0
        print("Escuchando...")
        audio = recognizer.listen(source, timeout=5)

    try:
        text = recognizer.recognize_google(audio, language="es-MX")
        print(f"Usted dijo: {text}")
        return text
    except sr.UnknownValueError:
        await speak("No entendí")
        return None
    except sr.RequestError as e:
        print(f"Error al conectar con el servicio de reconocimiento de voz: {e}")
        return None

# Convertir texto a voz
async def speak(texto_decir):
    tts = edge_tts.Communicate(text=texto_decir, voice="es-MX-DaliaNeural")
    await tts.save("output.mp3")

    pygame.mixer.init()
    pygame.mixer.music.load("output.mp3")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        await asyncio.sleep(1)

    pygame.mixer.music.stop()
    pygame.mixer.quit()
    os.remove("output.mp3")

# Buscar canciones y playlists
def search_spotify(query):
    result_track = sp.search(q=query, type='track', limit=3)
    if result_track and 'tracks' in result_track and result_track['tracks']['items']:
        track = result_track['tracks']['items'][0]
        print(f"Canción encontrada: {track['name']}")
        return 'track', track['uri']

    result_playlist = sp.search(q=query, type='playlist', limit=3)
    if result_playlist and 'playlists' in result_playlist and result_playlist['playlists']['items']:
        playlist = result_playlist['playlists']['items'][0]
        print(f"Playlist encontrada: {playlist['name']}")
        return 'playlist', playlist['uri']

    print("No encontré la canción o playlist.")
    return None, None

def play_music(tipo, uri):
    devices = sp.devices()
    if devices['devices']:
        device_id = devices['devices'][0]['id']
        if tipo == 'playlist':
            sp.start_playback(device_id=device_id, context_uri=uri)
        elif tipo == 'track':
            sp.start_playback(device_id=device_id, uris=[uri])
        print("Reproduciendo...")
    else:
        print("No hay dispositivos disponibles.")

# Función principal que gestiona el flujo
def verificar_sesion():
    token_info = sp.cache_handler.get_cached_token()
    if token_info and token_info["access_token"]:
        return True
    return False

# Crear y ejecutar el servidor Flask en un hilo
def run_flask():
    app.run(host='0.0.0.0', port=8888)

async def main():
    # Ejecutar Flask en un hilo
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True  # El hilo se cerrará cuando termine el programa principal
    flask_thread.start()

    time.sleep(3)  # Deja que Flask inicie

    # Verifica si la sesión de Spotify está activa
    if not verificar_sesion():
        await speak("No has iniciado sesión en Spotify. Redirigiéndote al flujo de autenticación.")
        auth_url = sp.get_authorize_url()
        webbrowser.open(auth_url)
        return

    await speak("Hola, ¿cómo estás?")
    while True:
        comando = await recognize_speech()
        comando = comando.lower() if comando else ""

        if "Aivona" in comando:
            while True:
                await speak("¿Qué quieres hacer?")
                comando = await recognize_speech()
                comando = comando.lower() if comando else ""

                if "salir" in comando or "cerrar" in comando or "chau" in comando or "adiós" in comando:
                    await speak("Adiós, que tengas un buen día.")
                    exit(0)

                elif "reproducir canción" in comando or ("reproducir" in comando and "playlist" not in comando):
                    await speak("¿Qué canción quieres que reproduzca?")
                    song_name = None
                    while not song_name:
                        song_name = await recognize_speech()
                        if song_name:
                            song_name = song_name.lower()

                    await speak("¿De qué artista?")
                    artist_name = None
                    while artist_name is None:
                        artist_name = await recognize_speech()
                        if artist_name:
                            artist_name = artist_name.lower()

                    query = f"track:{song_name}"
                    if artist_name != "none":
                        query += f" artist:{artist_name}"

                    result_track = sp.search(q=query, type='track', limit=1)

                    if result_track and result_track['tracks']['items']:
                        track = result_track['tracks']['items'][0]
                        play_music("track", track['uri'])
                    else:
                        await speak("No encontré la canción con ese artista o nombre.")
                    break

                elif "detener" in comando or "pausar" in comando:
                    sp.pause_playback()
                    await speak("Canción pausada.")
                    break

        await asyncio.sleep(5)

asyncio.run(main())
