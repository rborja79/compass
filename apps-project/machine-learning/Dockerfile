FROM python:3.11-slim

# Evita escribir archivos .pyc y usa salida sin buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instala dependencias necesarias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia requirements e instala dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . .

# Expone el puerto interno
EXPOSE 8000

# Verificación automática del servicio (opcional)
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
  CMD curl -fsS http://localhost:8008/health || exit 1

# Comando de arranque
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8008"]