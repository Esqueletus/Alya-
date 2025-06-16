import json
import os
from datetime import datetime, timezone

MEMORIA_ARCHIVO = "alya_memoria_larga.jsonl"

# Asegurar que el archivo exista
if not os.path.exists(MEMORIA_ARCHIVO):
    with open(MEMORIA_ARCHIVO, "w", encoding="utf-8") as f:
        pass

# Guardar entrada en memoria larga
def guardar_memoria_larga(role, content):
    entrada = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "role": role,
        "content": content
    }
    with open(MEMORIA_ARCHIVO, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")

# Leer toda la memoria larga (útil para debug o aprendizaje futuro)
def leer_memoria_larga():
    with open(MEMORIA_ARCHIVO, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
