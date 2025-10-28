
#!/usr/bin/env bash

# setup.sh - Script de inicialización del proyecto Compass

set -e  # Detener en caso de error

echo "🚀 Iniciando configuración del proyecto Compass..."

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
else
    echo -e "${RED}❌ Error: Archivo .env no encontrado${NC}"
    exit 1
fi

# Verificar que PROJECT_PATH esté definido
if [ -z "$PROJECT_PATH" ]; then
    echo -e "${RED}❌ Error: PROJECT_PATH no está definido en .env${NC}"
    exit 1
fi

echo -e "${BLUE}📁 PROJECT_PATH: $PROJECT_PATH${NC}"

# Crear estructura de directorios en apps-project
echo -e "${BLUE}📂 Creando estructura de directorios...${NC}"

mkdir -p "$PROJECT_PATH/apps-project/n8n/workflows"
mkdir -p "$PROJECT_PATH/apps-project/n8n/shared"
mkdir -p "$PROJECT_PATH/apps-project/scraping/logs"
mkdir -p "$PROJECT_PATH/apps-project/machine-learning/logs"
mkdir -p "$PROJECT_PATH/apps-project/anythingllm_storage"

echo -e "${GREEN}✅ Directorios creados${NC}"

# Crear red de Docker si no existe
echo -e "${BLUE}🐳 Configurando red Docker...${NC}"
if ! docker network inspect compass-network >/dev/null 2>&1; then
    docker network create compass-network
    echo -e "${GREEN}✅ Red compass-network creada${NC}"
else
    echo -e "${GREEN}✅ Red compass-network ya existe${NC}"
fi

# Clonar repositorio de AnythingLLM si no existe
echo -e "${BLUE}📦 Verificando repositorio de AnythingLLM...${NC}"
if [ ! -d "$PROJECT_PATH/anything-llm" ]; then
    echo -e "${YELLOW}⏳ Clonando AnythingLLM (esto puede tomar unos minutos)...${NC}"
    cd "$PROJECT_PATH"
    git clone https://github.com/Mintplex-Labs/anything-llm.git
    echo -e "${GREEN}✅ Repositorio de AnythingLLM clonado${NC}"

    # Información sobre cómo personalizar
    echo -e "${BLUE}💡 Para personalizar el frontend:${NC}"
    echo -e "   ${YELLOW}1. Modifica archivos en: anything-llm/frontend/src/${NC}"
    echo -e "   ${YELLOW}2. Actualiza docker-compose.yml para usar build local${NC}"
    echo -e "   ${YELLOW}3. Ejecuta: docker-compose build compass_agent${NC}"
else
    echo -e "${GREEN}✅ Repositorio de AnythingLLM ya existe${NC}"

    # Preguntar si se desea actualizar
    echo -e "${YELLOW}⚠️  ¿Deseas actualizar el repositorio? (y/N):${NC}"
    read -t 10 -n 1 UPDATE_REPO || UPDATE_REPO="n"
    echo ""

    if [[ $UPDATE_REPO =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🔄 Actualizando repositorio...${NC}"
        cd "$PROJECT_PATH/anything-llm"
        git pull
        echo -e "${GREEN}✅ Repositorio actualizado${NC}"
    else
        echo -e "${BLUE}ℹ️  Repositorio no actualizado${NC}"
    fi
fi

# Configurar AnythingLLM .env si no existe
ANYTHINGLLM_ENV="$PROJECT_PATH/apps-project/anythingllm_storage/.env"
if [ ! -f "$ANYTHINGLLM_ENV" ]; then
    echo -e "${BLUE}📝 Creando archivo .env para AnythingLLM...${NC}"

    # Verificar si openssl está disponible
    if command -v openssl >/dev/null 2>&1; then
        JWT_SECRET=$(openssl rand -base64 32)
    else
        # Alternativa sin openssl
        JWT_SECRET=$(cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
    fi

    cat > "$ANYTHINGLLM_ENV" << EOF
# AnythingLLM Configuration
STORAGE_DIR=/app/server/storage

# Configuración de autenticación
AUTH_TOKEN=
SERVER_PORT=3001

# Desactivar telemetría
DISABLE_TELEMETRY=true

# Modo multiusuario
AUTH_MODE=multi

# JWT Secret (generado automáticamente)
JWT_SECRET=${JWT_SECRET}

# LLM Provider (Ollama)
LLM_PROVIDER=ollama
OLLAMA_BASE_PATH=http://host.docker.internal:11434
OLLAMA_MODEL_PREF=gpt-oss:20b

# Embeddings
EMBEDDING_ENGINE=ollama
EMBEDDING_BASE_PATH=http://host.docker.internal:11434
EMBEDDING_MODEL_PREF=nomic-embed-text:latest

# Vector Database (Qdrant)
VECTOR_DB=qdrant
QDRANT_ENDPOINT=http://compass_qdrant:6333
QDRANT_API_KEY=yxor-andy-pznc-hnyc
EOF
    echo -e "${GREEN}✅ Archivo .env de AnythingLLM creado${NC}"
else
    echo -e "${YELLOW}⚠️  Archivo .env de AnythingLLM ya existe${NC}"
fi

echo -e "${GREEN}🎉 Setup completado exitosamente!${NC}"
echo ""
echo -e "${BLUE}Próximos pasos:${NC}"
echo -e "${GREEN}1. Levantar los servicios:${NC}"
echo -e "   ${YELLOW}docker-compose up -d${NC}"