# Compass - Setup Instructions

## 🚀 Instalación rápida (Todo en uno)

```bash
chmod +x start-compass.sh setup.sh setup-n8n-credentials.sh
./start-compass.sh
```

Este script ejecutará automáticamente:
1. ✅ Setup de directorios y repositorios
2. ✅ Inicio de todos los contenedores
3. ✅ Configuración de credenciales en n8n

## 📋 Instalación paso a paso

### 1. Setup inicial

```bash
chmod +x setup.sh
./setup.sh
```

### 2. Levantar servicios

```bash
docker-compose up -d
```

### 3. Configurar credenciales de n8n (esperar ~30 segundos)

```bash
chmod +x setup-n8n-credentials.sh
./setup-n8n-credentials.sh
```

## 🌐 Acceso a los servicios

- **n8n**: http://localhost:5678
  - Email: compass@unisabana.edu.co
  - Password: yxor-andy-pznc-hnyc
  - **Credenciales pre-configuradas**:
    - ✅ PostgreSQL n8n
    - ✅ PostgreSQL Compass
    - ✅ Qdrant Vector DB
    - ✅ Ollama
    - ✅ HTTP Auth interno

- **Open WebUI (Compass)**: http://localhost:3000
  - Email: compass@unisabana.edu.co
  - Password: yxor-andy-pznc-hnyc

- **PostgreSQL n8n**: localhost:5433
  - User: postgres
  - Password: yxor-andy-pznc-hnyc
  - Database: n8n_database

- **PostgreSQL Compass**: localhost:5434
  - User: postgres
  - Password: yxor-andy-pznc-hnyc
  - Database: compass_database

- **Qdrant Vector DB**: http://localhost:6333
  - Dashboard: http://localhost:6333/dashboard

## 📝 Gestión de workflows n8n

Los workflows se almacenan en: `apps-project/n8n/workflows/`

Para agregar workflows:
1. Exporta workflows desde n8n en formato JSON
2. Colócalos en `apps-project/n8n/workflows/`
3. Reinicia el contenedor: `docker-compose restart compass_n8n`

## 🔧 Comandos útiles

```bash
# Ver logs
docker-compose logs -f compass_app
docker-compose logs -f compass_n8n

# Reiniciar servicios
docker-compose restart

# Detener todo
docker-compose down

# Ver estado de contenedores
docker-compose ps

# Reconfigurar credenciales de n8n
./setup-n8n-credentials.sh
```

## 🔄 Reinicio completo (limpiar todo)

⚠️ **CUIDADO: Esto borrará todos los datos**

```bash
docker-compose down -v
./start-compass.sh
```

## 📁 Estructura de carpetas

```
Compass/
├── apps-project/
│   ├── n8n/
│   │   ├── workflows/          # Workflows de n8n (auto-importados)
│   │   └── shared/             # Archivos compartidos
│   ├── website/
│   │   └── shared/             # Archivos web compartidos
│   ├── scraping/               # Servicio de scraping
│   │   └── logs/
│   └── machine-learning/       # Servicio ML
│       └── logs/
├── open-webui/                 # Repo clonado de Open WebUI
├── docker-compose.yml
├── setup.sh                    # Setup inicial
├── setup-n8n-credentials.sh    # Configurar credenciales n8n
├── start-compass.sh            # Inicio completo automatizado
└── .env
```

## 🔐 Credenciales pre-configuradas en n8n

Las siguientes credenciales se crean automáticamente:

| Nombre | Tipo | Host | Base de datos | Usuario |
|--------|------|------|---------------|---------|
| Compass PostgreSQL n8n | postgres | compass_n8n_postgres_db | n8n_database | postgres |
| Compass PostgreSQL Main | postgres | compass_postgres_db | compass_database | postgres |
| Compass Qdrant | qdrantApi | compass_qdrant:6333 | - | - |
| Compass Ollama | ollamaApi | host.docker.internal:11434 | - | - |
| Compass Internal Services | httpBasicAuth | - | - | compass |

## 🐛 Troubleshooting

### n8n no inicia

```bash
docker-compose logs compass_n8n
docker-compose restart compass_n8n
```

### Credenciales no se crearon

```bash
# Esperar a que n8n esté listo
sleep 30
# Ejecutar de nuevo
./setup-n8n-credentials.sh
```

### Open WebUI no conecta con n8n

Verificar que el webhook de n8n esté activo en: http://localhost:5678

### Base de datos no conecta

```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps
docker-compose logs compass_postgres_db
```