#!/bin/bash

# setup.sh - Script de inicialización del proyecto Compass

set -e  # Detener en caso de error

echo " Iniciando configuración del proyecto Compass..."

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ Error: Archivo .env no encontrado"
    exit 1
fi

# Verificar que PROJECT_PATH esté definido
if [ -z "$PROJECT_PATH" ]; then
    echo "❌ Error: PROJECT_PATH no está definido en .env"
    exit 1
fi

echo -e "${BLUE} PROJECT_PATH: $PROJECT_PATH${NC}"

# Crear estructura de directorios en apps-project
echo -e "${BLUE} Creando estructura de directorios...${NC}"

mkdir -p "$PROJECT_PATH/apps-project/n8n/workflows"
mkdir -p "$PROJECT_PATH/apps-project/n8n/shared"
mkdir -p "$PROJECT_PATH/apps-project/website"
mkdir -p "$PROJECT_PATH/apps-project/scraping/logs"
mkdir -p "$PROJECT_PATH/apps-project/machine-learning/logs"
mkdir -p "$PROJECT_PATH/open-webui"

echo -e "${GREEN}✅ Directorios creados${NC}"

# Clonar o actualizar Open WebUI
echo -e "${BLUE} Configurando Open WebUI...${NC}"

if [ -d "$PROJECT_PATH/open-webui/.git" ]; then
    echo "Open WebUI ya existe, actualizando..."
    cd "$PROJECT_PATH/open-webui"
    git pull
else
    echo "Clonando Open WebUI..."
    cd "$PROJECT_PATH"
    git clone https://github.com/open-webui/open-webui.git
fi

echo -e "${GREEN}✅ Open WebUI configurado${NC}"

# Crear workflows de ejemplo si no existen
WORKFLOWS_DIR="$PROJECT_PATH/n8n/workflows"
if [ ! "$(ls -A $WORKFLOWS_DIR)" ]; then
    echo -e "${BLUE} Creando workflow de ejemplo...${NC}"
    cat > "$WORKFLOWS_DIR/example-workflow.json" << 'EOF'
{
  "name": "Example Workflow",
  "nodes": [
    {
      "parameters": {},
      "name": "Start",
      "type": "n8n-nodes-base.start",
      "typeVersion": 1,
      "position": [250, 300]
    }
  ],
  "connections": {},
  "active": false,
  "settings": {},
  "id": "1"
}
EOF
    echo -e "${GREEN}✅ Workflow de ejemplo creado${NC}"
else
    echo -e "${GREEN}✅ Workflows ya existen${NC}"
fi

# Crear red de Docker si no existe
echo -e "${BLUE} Configurando red Docker...${NC}"
if ! docker network inspect compass-network >/dev/null 2>&1; then
    docker network create compass-network
    echo -e "${GREEN}✅ Red compass-network creada${NC}"
else
    echo -e "${GREEN}✅ Red compass-network ya existe${NC}"
fi

# Crear archivo de configuración para Open WebUI
echo -e "${BLUE}⚙️  Creando configuración de Open WebUI...${NC}"
cat > "$PROJECT_PATH/open-webui/config.json" << 'EOF'
{
  "default_user": {
    "email": "compass@unisabana.edu.co",
    "password": "yxor-andy-pznc-hnyc",
    "name": "Compass Admin"
  }
}
EOF

echo -e "${GREEN}✅ Configuración completa${NC}"
echo ""
echo -e "${GREEN} Setup completado. Ahora puedes ejecutar:${NC}"
echo -e "${BLUE}   docker-compose up -d${NC}"