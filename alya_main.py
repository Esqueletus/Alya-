import os
import base64
import asyncio
from datetime import datetime
from github import Github
import discord

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "Esqueletus"
REPO_NAME = "Alya24-7"
BACKUP_DIR = "alya_backups"

os.makedirs(BACKUP_DIR, exist_ok=True)

ALYA_FILENAME = os.path.abspath(__file__)

def crear_backup_local(ruta_original: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    nombre_backup = f"alya_backup_{timestamp}.py"
    ruta_backup = os.path.join(BACKUP_DIR, nombre_backup)

    with open(ruta_original, "r", encoding="utf-8") as origen:
        contenido = origen.read()

    with open(ruta_backup, "w", encoding="utf-8") as backup:
        backup.write(contenido)

    return ruta_backup

def subir_backup_github(ruta_backup: str):
    if not GITHUB_TOKEN:
        print("⚠️ No se encontró token de GitHub. No se subirá el backup.")
        return

    g = Github(GITHUB_TOKEN)
    repo = g.get_user(REPO_OWNER).get_repo(REPO_NAME)

    with open(ruta_backup, "rb") as f:
        contenido_base64 = base64.b64encode(f.read()).decode("utf-8")

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ruta_github = f"backup/{os.path.basename(ruta_backup)}"

    try:
        repo.create_file(
            ruta_github,
            f"Backup automático de Alya ({fecha})",
            contenido_base64,
        )
        print(f"✅ Backup subido a GitHub: {ruta_github}")
    except Exception as e:
        print(f"❌ Error subiendo backup a GitHub: {e}")

# Ejemplo mínimo de bot discord

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

    if "alya" in message.content.lower():
        # Crear backup local
        backup_path = crear_backup_local(ALYA_FILENAME)

        # Subir backup en un hilo separado sin bloquear
        await asyncio.to_thread(subir_backup_github, backup_path)

        await message.channel.send("Backup creado y subido a GitHub ✅")

# Ejecutar bot con tu token
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
client.run(DISCORD_TOKEN)

