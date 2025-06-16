import os
import shutil
import datetime
import ast

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
