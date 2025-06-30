# Social Listening Dashboard - Docker Commands

## Production Environment
```bash
# Run production container
docker compose up -d

# Stop production container
docker compose down

# Rebuild and run production
docker compose up --build -d
```

## Development Environment
```bash
# Run development container (with hot reload)
docker compose -f docker-compose.dev.yml up -d

# Stop development container
docker compose -f docker-compose.dev.yml down

# Rebuild and run development
docker compose -f docker-compose.dev.yml up --build -d
```

## Troubleshooting
```bash
# Clean Docker cache if build fails
docker system prune -f

# Remove all containers and rebuild from scratch
docker compose down
docker system prune -af
docker compose up --build -d
```

## Logs
```bash
# View production logs
docker compose logs -f social-listening

# View development logs
docker compose -f docker-compose.dev.yml logs -f social-listening-dev
```

## Access Points
```bash
# Application URLs (after starting containers)
# Web Interface: http://localhost:8002
# API Documentation: http://localhost:8002/docs
# API Endpoints: http://localhost:8002/api/v1/

# Check container status
docker compose ps

# Health check
curl http://localhost:8002
```
