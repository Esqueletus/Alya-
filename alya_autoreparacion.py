import os
import shutil
import datetime
import ast
import aiohttp
from alya_memoria import guardar_memoria_larga

async def analizar_codigo_con_groq(codigo, system_prompt, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = f"""Eres una IA que puede autoreprogramarse. Analiza el siguiente código de un bot de Discord en Python.
Evalúa si:
- Tiene errores
- Es seguro
- Mejora funciones como memoria, autoreparación o conversación

Responde SÓLO con:
- ✅ Si es seguro y mejora el código
- ⚠️ Si es correcto pero no mejora
- ❌ Si tiene errores o es peligroso

---CÓDIGO---
{codigo}
---FIN---
"""

    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data) as resp:
            try:
                res = await resp.json()
                texto = res["choices"][0]["message"]["content"]
                guardar_memoria_larga("assistant", f"Groq analizó código y respondió: {texto}")
                return texto.strip()
            except Exception as e:
                return f"❌ Error analizando código: {e}"


# Validar que sea código Python válido
def codigo_es_valido(codigo: str) -> bool:
    try:
        ast.parse(codigo)
        return True
    except SyntaxError:
        return False

# Revisar si mejora cosas importantes (por ejemplo, si contiene memoria o respuesta)
def contiene_funciones_utiles(codigo: str) -> bool:
    funciones_relevantes = ["on_message", "get_groq_reply", "guardar_memoria"]
    return any(f in codigo for f in funciones_relevantes)

ARCHIVO_PRINCIPAL = "alya_main.py"
BACKUP_DIR = "reparaciones_backup"

# Crear carpeta de backup si no existe
os.makedirs(BACKUP_DIR, exist_ok=True)

# Guardar respaldo antes de modificar
def respaldar_archivo():
    fecha = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    nombre_backup = f"{BACKUP_DIR}/alya_backup_{fecha}.py"
    shutil.copy(ARCHIVO_PRINCIPAL, nombre_backup)
    return nombre_backup

# Aplicar mejora/autoreparación
def aplicar_mejora(nuevo_codigo: str) -> str:
    if "import discord" not in nuevo_codigo or "client.run" not in nuevo_codigo:
        return "❌ El código no parece válido o está incompleto. Autoreparación cancelada."

    respaldo = respaldar_archivo()
    try:
        with open(ARCHIVO_PRINCIPAL, "w", encoding="utf-8") as f:
            f.write(nuevo_codigo)
        return f"✅ Código actualizado correctamente. Backup: {respaldo}"
    except Exception as e:
        return f"❌ Error al guardar el nuevo código: {e}"
