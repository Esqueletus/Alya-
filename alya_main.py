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
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # Aquí pon tu token openrouter (DeepSeek)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))

REPO_OWNER = "Esqueletus"
REPO_NAME = "Alya-"
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

async def get_openrouter_reply(message_content, memory_context=[]):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "Eres Alya, una IA tsundere, directa, honesta y amorosa, que responde en español, "
        "con humor y firmeza, recuerda contexto, limita sus respuestas a 800 caracteres y evita exageraciones."
    )

    # Construir mensajes para la API
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(memory_context[-20:])
    messages.append({"role": "user", "content": message_content})

    data = {
        "model": "deepseek",
        "messages": messages,
        "temperature": 0.7
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data) as resp:
                if resp.status != 200:
                    return "No me molestes con eso, no puedo responder ahora mismo. Pregunta otra cosa."
                res = await resp.json()
                if "choices" in res and len(res["choices"]) > 0:
                    respuesta = res["choices"][0]["message"]["content"]
                    if len(respuesta) > MAX_RESPONSE_CHARS:
                        # Cortar sin romper la última frase
                        respuesta = respuesta[:MAX_RESPONSE_CHARS].rsplit('.', 1)[0] + '.'
                    return respuesta
                else:
                    return "No me molestes con eso, no puedo responder ahora mismo. Pregunta otra cosa."
        except Exception as e:
            print(f"[ERROR] get_openrouter_reply Exception: {e}")
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
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_user(REPO_OWNER).get_repo(REPO_NAME)
        with open(ruta_backup, "rb") as f:
            contenido_b64 = base64.b64encode(f.read()).decode()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ruta_github = f"backup/{os.path.basename(ruta_backup)}"
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

    # Comando backup sólo para usuario permitido
    if message.author.id == ALLOWED_USER_ID and content.startswith("!backup"):
        backup_path = crear_backup_local(os.path.abspath(__file__))
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, subir_backup_github, backup_path)
        # No enviar mensaje en canal para no molestar
        print("Backup creado y subido a GitHub ✅")
        return

    if any(palabra in content for palabra in ["alya", "aly", "alys"]):
        guardar_memoria("user", message.content)
        respuesta = await get_openrouter_reply(message.content, memory_context=short_term_memory)
        guardar_memoria("assistant", respuesta)
        await message.channel.send(respuesta)

client.run(DISCORD_TOKEN)
