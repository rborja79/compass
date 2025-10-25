
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
mkdir -p "$PROJECT_PATH/apps-project/website/shared"
mkdir -p "$PROJECT_PATH/apps-project/scraping/logs"
mkdir -p "$PROJECT_PATH/apps-project/machine-learning/logs"
mkdir -p "$PROJECT_PATH/open-webui"

echo -e "${GREEN}✅ Directorios creados${NC}"

# Clonar o actualizar Open WebUI
echo -e "${BLUE}🌐 Configurando Open WebUI...${NC}"

if [ -d "$PROJECT_PATH/open-webui/.git" ]; then
    echo "Open WebUI ya existe, actualizando..."
    cd "$PROJECT_PATH/open-webui"
    git pull origin main || git pull
    cd "$PROJECT_PATH"
else
    echo "Clonando Open WebUI..."
    cd "$PROJECT_PATH"
    git clone https://github.com/open-webui/open-webui.git "$PROJECT_PATH/open-webui"
fi

echo -e "${GREEN}✅ Open WebUI configurado${NC}"

# Crear workflows de ejemplo si no existen
WORKFLOWS_DIR="$PROJECT_PATH/apps-project/n8n/workflows"
if [ ! "$(ls -A $WORKFLOWS_DIR 2>/dev/null)" ]; then
    echo -e "${BLUE}📝 Creando workflow de ejemplo...${NC}"
    cat > "$WORKFLOWS_DIR/example-workflow.json" << 'EOF'
{
  "name": "Example Workflow - Compass",
  "nodes": [
    {
      "parameters": {},
      "name": "Start",
      "type": "n8n-nodes-base.start",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "content": "=## Bienvenido a Compass\n\nEste es un workflow de ejemplo.\nLas credenciales de bases de datos ya están configuradas.",
        "height": 464.6333333333333,
        "width": 567.5666666666665
      },
      "name": "Sticky Note",
      "type": "n8n-nodes-base.stickyNote",
      "typeVersion": 1,
      "position": [380, 240]
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
echo -e "${BLUE}🐳 Configurando red Docker...${NC}"
if ! docker network inspect compass-network >/dev/null 2>&1; then
    docker network create compass-network
    echo -e "${GREEN}✅ Red compass-network creada${NC}"
else
    echo -e "${GREEN}✅ Red compass-network ya existe${NC}"
fi

# Hacer ejecutable el script de credenciales
chmod +x "$PROJECT_PATH/setup-n8n-credentials.sh" 2>/dev/null || true

echo -e "${GREEN}🎉 Setup completado exitosamente!${NC}"
echo ""
echo -e "${BLUE}Próximos pasos:${NC}"
echo -e "${GREEN}1. Levantar los servicios:${NC}"
echo -e "   ${YELLOW}docker-compose up -d${NC}"
echo ""
echo -e "${GREEN}2. Configurar credenciales de n8n (esperar ~30 segundos):${NC}"
echo -e "   ${YELLOW}./setup-n8n-credentials.sh${NC}"
echo ""
echo -e "${BLUE}Servicios disponibles:${NC}"
echo -e "${GREEN}   - n8n: http://localhost:5678${NC}"
echo -e "${GREEN}   - Open WebUI: http://localhost:3000${NC}"
echo -e "${GREEN}   - PostgreSQL n8n: localhost:5433${NC}"
echo -e "${GREEN}   - PostgreSQL Compass: localhost:5434${NC}"
echo -e "${GREEN}   - Qdrant: http://localhost:6333${NC}"
echo ""
echo -e "${BLUE}Credenciales:${NC}"
echo -e "${GREEN}   Email: compass@unisabana.edu.co${NC}"
echo -e "${GREEN}   Password: yxor-andy-pznc-hnyc${NC}"