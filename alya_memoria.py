import json
import os
from datetime import datetime, timezone

MEMORIA_ARCHIVO = "alya_memoria_larga.jsonl"

# Crear archivo si no existe
if not os.path.exists(MEMORIA_ARCHIVO):
    with open(MEMORIA_ARCHIVO, "w", encoding="utf-8") as f:
        pass

# Guardar entrada nueva
def guardar_memoria_larga(role, content):
    entrada = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "role": role,
        "content": content
    }
    with open(MEMORIA_ARCHIVO, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")

# Leer memoria completa
def leer_memoria_larga():
    with open(MEMORIA_ARCHIVO, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

# Buscar dentro de la memoria larga (retorna hasta 5 coincidencias)
def buscar_en_memoria(query, max_resultados=5):
    memoria = leer_memoria_larga()
    resultados = []
    for entrada in memoria:
        if query.lower() in entrada["content"].lower():
            resultados.append(entrada)
            if len(resultados) >= max_resultados:
                break
# Buscar memoria relevante automáticamente (para IA)
def contexto_relacionado(query, max_resultados=3):
    memoria = leer_memoria_larga()
    resultados = []
    for entrada in reversed(memoria):
        if entrada["role"] == "user" and query.lower() in entrada["content"].lower():
            resultados.append(f'{entrada["role"]}: {entrada["content"]}')
        if entrada["role"] == "assistant" and query.lower() in entrada["content"].lower():
            resultados.append(f'{entrada["role"]}: {entrada["content"]}')
        if len(resultados) >= max_resultados:
            break
    return resultados[::-1]  # Más antiguo arriba
