import os
import json
import base64
import asyncio
from datetime import datetime, timezone
import aiohttp
from github import Github
import discord

# Variables de entorno
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))

REPO_OWNER = "Esqueletus"
REPO_NAME = "Alya24-7"
BACKUP_DIR = "alya_backups"

MAX_RESPONSE_CHARS = 800
LONG_TERM_MEMORY_FILE = "alya_long_term_memory.json"
SHORT_TERM_MEMORY_MAX = 100
SHORT_TERM_MEMORY_TRIM_TO = 50

os.makedirs(BACKUP_DIR, exist_ok=True)

# Memoria larga y corta
if not os.path.exists(LONG_TERM_MEMORY_FILE):
    with open(LONG_TERM_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

with open(LONG_TERM_MEMORY_FILE, "r", encoding="utf-8") as f:
    long_term_memory = json.load(f)

short_term_memory = []

def guardar_memoria(role, content):
    mensaje = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    short_term_memory.append(mensaje)
    long_term_memory.append(mensaje)
    if len(short_term_memory) > SHORT_TERM_MEMORY_MAX:
        del short_term_memory[:len(short_term_memory) - SHORT_TERM_MEMORY_TRIM_TO]
    with open(LONG_TERM_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(long_term_memory, f, ensure_ascii=False, indent=2)

async def get_groq_reply(message_content, memory_context=[]):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    modelos = ["mixtral-8x7b-32768", "llama3-8b-8192", "gemma-7b-it"]

    for modelo in modelos:
        data = {
            "model": modelo,
            "messages": [
                {"role": "system", "content": (
                    "Eres Alya, una IA tsundere, directa, honesta y amorosa, que responde en español, "
                    "con humor y firmeza, recuerda contexto, limita sus respuestas a 800 caracteres y evita exageraciones."
                )},
                *memory_context[-20:],
                {"role": "user", "content": message_content}
            ]
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data) as resp:
                    res = await resp.json()
                    if "choices" in res and len(res["choices"]) > 0:
                        respuesta = res["choices"][0]["message"]["content"]
                        # Limitar a MAX_RESPONSE_CHARS caracteres
                        if len(respuesta) > MAX_RESPONSE_CHARS:
                            respuesta = respuesta[:MAX_RESPONSE_CHARS].rsplit('.',1)[0] + '.'
                        return respuesta
            except Exception:
                continue
    # Mensaje tsundere si fallan todos los modelos
    return "No me molestes con eso, no puedo responder ahora mismo. Pregunta otra cosa."

def crear_backup_local(ruta_original):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    nombre_backup = f"alya_backup_{timestamp}.py"
    ruta_backup = os.path.join(BACKUP_DIR, nombre_backup)
    with open(ruta_original, "r", encoding="utf-8") as origen:
        contenido = origen.read()
    with open(ruta_backup, "w", encoding="utf-8") as backup:
        backup.write(contenido)
    return ruta_backup

def subir_backup_github(ruta_backup):
    if not GITHUB_TOKEN:
        print("⚠️ No se encontró token de GitHub, no se subirá el backup.")
        return
    g = Github(GITHUB_TOKEN)
    repo = g.get_user(REPO_OWNER).get_repo(REPO_NAME)
    with open(ruta_backup, "rb") as f:
        contenido_b64 = base64.b64encode(f.read()).decode()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ruta_github = f"backup/{os.path.basename(ruta_backup)}"
    try:
        repo.create_file(ruta_github, f"Backup automático Alya ({fecha})", contenido_b64)
        print(f"✅ Backup subido a GitHub: {ruta_github}")
    except Exception as e:
        print(f"❌ Error subiendo backup a GitHub: {e}")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"[✅] Alya está online como {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.lower()

    if message.author.id == ALLOWED_USER_ID and content.startswith("!backup"):
        backup_path = crear_backup_local(os.path.abspath(__file__))
        # Ejecutar la subida a GitHub sin bloquear el event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, subir_backup_github, backup_path)
        await message.channel.send("Backup creado y subido a GitHub ✅")
        return

    # Solo responde si mencionan "alya" en el mensaje
    if any(palabra in content for palabra in ["alya", "aly", "alys"]):
        guardar_memoria("user", message.content)
        respuesta = await get_groq_reply(message.content, memory_context=short_term_memory)
        guardar_memoria("assistant", respuesta)
        await message.channel.send(respuesta)

client.run(DISCORD_TOKEN)
