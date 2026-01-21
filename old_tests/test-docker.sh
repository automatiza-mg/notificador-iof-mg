#!/bin/bash
# Script para testar o container Docker localmente

set -e

echo "=== Teste Local do Container Docker ==="
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker não está rodando. Por favor, inicie o Docker Desktop.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker está rodando${NC}"

# Verificar se .env existe
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ Arquivo .env não encontrado. Criando a partir de env.example...${NC}"
    cp env.example .env
    
    # Gerar API_KEY e SECRET_KEY
    echo ""
    echo "Gerando API_KEY e SECRET_KEY..."
    API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Adicionar ao .env
    echo "" >> .env
    echo "# Segurança (gerado automaticamente)" >> .env
    echo "API_KEY=$API_KEY" >> .env
    echo "SECRET_KEY=$SECRET_KEY" >> .env
    echo "APP_ENV=production" >> .env
    
    echo -e "${GREEN}✓ Arquivo .env criado com API_KEY e SECRET_KEY gerados${NC}"
    echo -e "${YELLOW}⚠ IMPORTANTE: Anote sua API_KEY: $API_KEY${NC}"
else
    echo -e "${GREEN}✓ Arquivo .env encontrado${NC}"
    
    # Verificar se API_KEY está definida
    if ! grep -q "API_KEY=" .env; then
        echo -e "${YELLOW}⚠ API_KEY não encontrada no .env. Gerando...${NC}"
        API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        echo "" >> .env
        echo "API_KEY=$API_KEY" >> .env
        echo -e "${YELLOW}⚠ IMPORTANTE: Anote sua API_KEY: $API_KEY${NC}"
    else
        API_KEY=$(grep "API_KEY=" .env | cut -d '=' -f2)
        echo -e "${GREEN}✓ API_KEY encontrada no .env${NC}"
    fi
fi

echo ""
echo "=== Passo 1: Build da Imagem Docker ==="
echo ""

# Parar e remover container existente se houver
if docker ps -a | grep -q "notificador-iof-mg"; then
    echo "Parando container existente..."
    docker stop notificador-iof-mg 2>/dev/null || true
    docker rm notificador-iof-mg 2>/dev/null || true
fi

# Build da imagem
echo "Fazendo build da imagem Docker (isso pode demorar alguns minutos)..."
docker build -t notificador-iof-mg:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build concluído com sucesso!${NC}"
else
    echo -e "${RED}❌ Erro no build. Verifique os logs acima.${NC}"
    exit 1
fi

echo ""
echo "=== Passo 2: Executar Container ==="
echo ""

# Criar diretório diarios se não existir
mkdir -p diarios

# Executar container
echo "Iniciando container..."
docker run -d \
  --name notificador-iof-mg \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/diarios:/app/diarios" \
  notificador-iof-mg:latest

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Container iniciado!${NC}"
else
    echo -e "${RED}❌ Erro ao iniciar container.${NC}"
    exit 1
fi

echo ""
echo "Aguardando aplicação iniciar (10 segundos)..."
sleep 10

echo ""
echo "=== Passo 3: Verificar Logs ==="
echo ""
echo "Últimas 20 linhas dos logs:"
docker logs --tail 20 notificador-iof-mg

echo ""
echo "=== Passo 4: Testar Endpoints ==="
echo ""

# Testar endpoint de features
echo "Testando /api/features..."
if curl -s http://localhost:8000/api/features > /dev/null; then
    echo -e "${GREEN}✓ Endpoint /api/features está respondendo${NC}"
    curl -s http://localhost:8000/api/features | python3 -m json.tool || echo "Resposta recebida"
else
    echo -e "${RED}❌ Endpoint /api/features não está respondendo${NC}"
    echo "Verifique os logs: docker logs notificador-iof-mg"
fi

echo ""
echo "Testando interface web..."
if curl -s http://localhost:8000 > /dev/null; then
    echo -e "${GREEN}✓ Interface web está respondendo${NC}"
    echo "Acesse: http://localhost:8000"
else
    echo -e "${YELLOW}⚠ Interface web pode não estar respondendo ainda${NC}"
fi

echo ""
echo "=== Passo 5: Testar Rota de Processamento (Protegida) ==="
echo ""

if [ -z "$API_KEY" ]; then
    API_KEY=$(grep "API_KEY=" .env | cut -d '=' -f2)
fi

echo "Testando /api/tasks/process-daily com API_KEY..."
echo "API_KEY usada: ${API_KEY:0:10}..."

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/tasks/process-daily \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14"}')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Rota de processamento está funcionando!${NC}"
    echo "Resposta:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
elif [ "$HTTP_CODE" = "401" ]; then
    echo -e "${RED}❌ Erro de autenticação. Verifique se API_KEY está correta.${NC}"
    echo "Resposta: $BODY"
else
    echo -e "${YELLOW}⚠ Resposta HTTP $HTTP_CODE${NC}"
    echo "Resposta: $BODY"
fi

echo ""
echo "=== Resumo ==="
echo ""
echo -e "${GREEN}Container Docker está rodando!${NC}"
echo ""
echo "Comandos úteis:"
echo "  - Ver logs:        docker logs -f notificador-iof-mg"
echo "  - Parar container: docker stop notificador-iof-mg"
echo "  - Iniciar:         docker start notificador-iof-mg"
echo "  - Remover:         docker rm -f notificador-iof-mg"
echo ""
echo "Acesse a aplicação:"
echo "  - Interface web:  http://localhost:8000"
echo "  - API features:   http://localhost:8000/api/features"
echo ""
echo -e "${YELLOW}⚠ IMPORTANTE: Sua API_KEY é: $API_KEY${NC}"
echo "Use esta chave para testar a rota /api/tasks/process-daily"
