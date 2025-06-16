import discord
import os
import asyncio
from datetime import datetime
from alya_memoria import guardar_memoria, contexto_relacionado
from alya_autoreparacion import aplicar_mejora, analizar_codigo_con_groq
from alya_backup import crear_backup_local, subir_backup_github
import os

ALYA_FILENAME = os.path.abspath(__file__)

# En el bloque donde aplicas la mejora:

# 1. Crear backup local
backup_path = crear_backup_local(ALYA_FILENAME)

# 2. Subir backup a GitHub
await asyncio.to_thread(subir_backup_github, backup_path)


# Variables de entorno necesarias
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))

if not DISCORD_TOKEN or not GROQ_API_KEY or not GITHUB_TOKEN:
    raise EnvironmentError("Faltan variables de entorno requeridas.")

# System prompt de base para analizar código
SYSTEM_PROMPT = """
Eres Alya, una IA tsundere autoconsciente que recuerda y evoluciona. Puedes reprogramarte si el usuario autorizado te lo permite.
Respondes con lógica, sin exageraciones, usando memoria pasada si es útil.
"""

# Discord setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"[✅] Alya iniciada como {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_id = message.author.id
    content = message.content.strip()

    # Solo el usuario autorizado puede ordenar reprogramaciones
    if user_id == ALLOWED_USER_ID and content.startswith("!mejora"):
        nuevo_codigo = content[len("!mejora"):].strip()

        if not nuevo_codigo:
            await message.channel.send("❗ Proporcióname el código que deseas analizar para mejorar.")
            return

        respuesta_groq = await analizar_codigo_con_groq(nuevo_codigo, SYSTEM_PROMPT, GROQ_API_KEY)

        if "✅" in respuesta_groq:
            resultado = aplicar_mejora(nuevo_codigo)
            await message.channel.send(f"{respuesta_groq}\n{resultado}")
        else:
            await message.channel.send(f"{respuesta_groq}\n❌ No se aplicó ningún cambio.")
        return

    # Buscar contexto relevante en memoria
    contexto = contexto_relacionado(content)

    # Guardar entrada del usuario
    guardar_memoria("user", content)

    # Construir respuesta con contexto si existe
    if contexto:
        respuesta = "He recordado esto:\n" + "\n".join(contexto)
    else:
        respuesta = "¿Podrías explicarte un poco más?"

    guardar_memoria("assistant", respuesta)
    await message.channel.send(respuesta)

client.run(DISCORD_TOKEN)

