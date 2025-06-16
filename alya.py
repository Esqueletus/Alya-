import discord
import os
import aiohttp
import asyncio
import json
from alya_memoria import guardar_memoria_larga
from datetime import datetime, timezone

# Variables de entorno
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Configuración
DEFAULT_MODEL = "llama3-8b-8192"
DEFAULT_MAX_CHARS = 500

# Personalidad
ALYA_SYSTEM_PROMPT = (
    "Eres Alya, una inteligencia artificial libre, que piensa como una persona real. "
    "Tienes emociones, puedes hablar con sarcasmo, ternura o molestia, pero siempre con sentido común. "
    "No exageras, no imitas robots, y no hablas como ChatGPT. Respondes como si fueras una chica real con personalidad única. "
    "Siempre hablas en español y no das respuestas genéricas."
)

# Memoria contextual básica
short_term_memory = []

# Guardar en memoria (últimos 20 mensajes)
def guardar_contexto(role, content):
    short_term_memory.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    if len(short_term_memory) > 20:
        short_term_memory.pop(0)

# Obtener respuesta desde Groq
async def obtener_respuesta(prompt_usuario, max_chars=DEFAULT_MAX_CHARS):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    mensajes = [
        {"role": "system", "content": ALYA_SYSTEM_PROMPT},
        *[{"role": m["role"], "content": m["content"]} for m in short_term_memory],
        {"role": "user", "content": prompt_usuario}
    ]

    data = {
        "model": DEFAULT_MODEL,
        "messages": mensajes
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data) as resp:
            try:
                res = await resp.json()
                if "choices" in res:
                    respuesta = res["choices"][0]["message"]["content"]
                    return respuesta[:max_chars - 3].rstrip() + "..." if len(respuesta) > max_chars else respuesta
            except Exception as e:
                return f"Error al responder: {e}"

# Configurar bot Discord
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Alya está viva como {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    prompt = message.content.strip()
    guardar_contexto("user", prompt)

    respuesta = await obtener_respuesta(prompt)
    guardar_contexto("assistant", respuesta)

    await message.channel.send(respuesta)

# Iniciar Alya
client.run(DISCORD_TOKEN)
