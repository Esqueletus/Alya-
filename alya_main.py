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
REPO_NAME = "Alya-"
BACKUP_DIR = "alya_backups"

# Config
MAX_RESPONSE_CHARS = 800  # límite máximo de caracteres en respuesta

# Memoria archivos
LONG_TERM_MEMORY_FILE = "alya_long_term_memory.json"
SHORT_TERM_MEMORY_MAX = 100
SHORT_TERM_MEMORY_TRIM_TO = 50

# Inicializar directorios y archivos
os.makedirs(BACKUP_DIR, exist_ok=True)

for fpath, default_content in [
    (LONG_TERM_MEMORY_FILE, []),
]:
    if not os.path.exists(fpath):
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(default_content, f)

# Cargar memoria larga
with open(LONG_TERM_MEMORY_FILE, "r", encoding="utf-8") as f:
    long_term_memory = json.load(f)

short_term_memory = []

# Guardar memoria
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

# Crear backup local
def crear_backup_local(ruta_original):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    nombre_backup = f"alya_backup_{timestamp}.py"
    ruta_backup = os.path.join(BACKUP_DIR, nombre_backup)
    with open(ruta_original, "r", encoding="utf-8") as origen:
        contenido = origen.read()
    with open(ruta_backup, "w", encoding="utf-8") as backup:
        backup.write(contenido)
    return ruta_backup

# Subir backup a GitHub
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

# Llamar a Groq para obtener respuesta
async def get_groq_reply(user_message, memory_context):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {"role": "system", "content": "Eres Alya, una IA tsundere, honesta y directa. Responde en español, sin exagerar, con humor."},
            *memory_context[-20:],  # últimos 20 mensajes
            {"role": "user", "content": user_message}
        ]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data) as resp:
            if resp.status == 200:
                res_json = await resp.json()
                if "choices" in res_json and len(res_json["choices"]) > 0:
                    return res_json["choices"][0]["message"]["content"]
    return "Lo siento, no pude procesar tu solicitud."

# Limitar texto y resumir si es necesario
async def limitar_y_resumir(texto, max_chars=MAX_RESPONSE_CHARS):
    if len(texto) <= max_chars:
        return texto
    # Si es muy largo, pedimos a Groq que resuma en max_chars
    prompt = (
        f"Resume el siguiente texto en máximo {max_chars} caracteres, "
        "manteniendo la esencia y sin perder información importante:\n\n"
        f"{texto}"
    )
    resumen = await get_groq_reply(prompt, [])
    if len(resumen) > max_chars:
        resumen = resumen[:max_chars]  # forzamos límite estricto si falla resumen
    return resumen

# Discord setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Alya está online como {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content_lower = message.content.lower()

    # Comando backup SOLO para usuario autorizado
    if message.author.id == ALLOWED_USER_ID and content_lower.strip() == "!backup":
        backup_path = crear_backup_local(os.path.abspath(__file__))
        await asyncio.to_thread(subir_backup_github, backup_path)
        await message.channel.send("Backup creado y subido a GitHub ✅")
        return

    # Responder solo si mencionan a Alya
    if "alya" in content_lower:
        guardar_memoria("user", message.content)
        # Preparamos contexto para Groq (solo roles y contenido)
        memoria_contexto = [{"role": m["role"], "content": m["content"]} for m in short_term_memory]
        respuesta_raw = await get_groq_reply(message.content, memoria_contexto)
        respuesta = await limitar_y_resumir(respuesta_raw, MAX_RESPONSE_CHARS)
        guardar_memoria("assistant", respuesta)
        await message.channel.send(respuesta)

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)


