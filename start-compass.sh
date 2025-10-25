#!/usr/bin/env bash

# start-compass.sh - Inicia todo el stack de Compass

set -e

echo "🚀 Iniciando Compass Stack completo..."

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Ejecutar setup inicial
echo -e "${BLUE}📦 Paso 1: Setup inicial...${NC}"
chmod +x setup.sh
./setup.sh

# 2. Levantar contenedores
echo -e "${BLUE}🐳 Paso 2: Levantando contenedores...${NC}"
docker-compose up -d

# 3. Esperar a que n8n esté listo
echo -e "${BLUE}⏳ Paso 3: Esperando a que n8n esté listo (30 segundos)...${NC}"
sleep 30

# 4. Configurar credenciales
echo -e "${BLUE}🔐 Paso 4: Configurando credenciales en n8n...${NC}"
chmod +x setup-n8n-credentials.sh
./setup-n8n-credentials.sh

echo -e "${GREEN}✅ ¡Compass Stack iniciado completamente!${NC}"
echo ""
echo -e "${BLUE}Accede a:${NC}"
echo -e "${GREEN}  🔗 n8n: http://localhost:5678${NC}"
echo -e "${GREEN}  🔗 Compass: http://localhost:3000${NC}"
echo ""
echo -e "${BLUE}Credenciales:${NC}"
echo -e "${GREEN}  📧 Email: compass@unisabana.edu.co${NC}"
echo -e "${GREEN}  🔑 Password: yxor-andy-pznc-hnyc${NC}"