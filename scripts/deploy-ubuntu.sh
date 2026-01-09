#!/bin/bash
# ===========================================
# Script de Deploy Automático no Ubuntu
# Compatível com: Ubuntu Server
# ===========================================

set -e

GITHUB_REPO="${1:-}"
INSTALL_DIR="${2:-/opt/controle-ferias}"

if [ -z "$GITHUB_REPO" ]; then
    echo "❌ Uso: ./scripts/deploy-ubuntu.sh <URL_DO_GITHUB> [diretorio]"
    echo ""
    echo "Exemplo:"
    echo "  ./scripts/deploy-ubuntu.sh https://github.com/usuario/controle-ferias.git"
    echo "  ./scripts/deploy-ubuntu.sh https://github.com/usuario/controle-ferias.git /home/usuario/apps"
    exit 1
fi

echo "🚀 Deploy Automático - Sistema de Controle de Férias"
echo "====================================================="
echo ""

# Verifica Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado!"
    echo "   Instale com: sudo apt install docker.io docker-compose"
    exit 1
fi

# Cria diretório de instalação
echo "📁 Criando diretório de instalação..."
sudo mkdir -p "$(dirname $INSTALL_DIR)"
if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Diretório já existe: $INSTALL_DIR"
    read -p "Continuar e atualizar? (s/n): " confirm
    if [ "$confirm" != "s" ]; then
        exit 0
    fi
else
    sudo mkdir -p "$INSTALL_DIR"
fi

# Clona ou atualiza o repositório
echo ""
echo "📥 Clonando/Atualizando repositório..."
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "   Atualizando repositório existente..."
    cd "$INSTALL_DIR"
    git pull origin main || git pull origin master
else
    echo "   Clonando novo repositório..."
    sudo git clone "$GITHUB_REPO" "$INSTALL_DIR"
    sudo chown -R $USER:$USER "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# Configura .env
if [ ! -f .env ]; then
    echo ""
    echo "⚙️  Configurando .env..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "   ✅ Arquivo .env criado a partir do exemplo"
        echo "   ⚠️  IMPORTANTE: Edite o .env antes de iniciar!"
        echo "      nano $INSTALL_DIR/.env"
    else
        echo "   ⚠️  Arquivo .env.example não encontrado"
    fi
else
    echo ""
    echo "✅ Arquivo .env já existe"
fi

# Ajusta permissões
echo ""
echo "🔐 Ajustando permissões..."
sudo chown -R $USER:$USER "$INSTALL_DIR"
chmod +x scripts/*.sh
chmod 600 .env 2>/dev/null || true

# Verifica Docker Compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Docker Compose não encontrado!"
    exit 1
fi

# Pergunta se quer iniciar agora
echo ""
read -p "🚀 Iniciar containers agora? (s/n): " start_now

if [ "$start_now" = "s" ]; then
    echo ""
    echo "🔨 Construindo e iniciando containers..."
    $DOCKER_COMPOSE up -d --build
    
    echo ""
    echo "⏳ Aguardando containers iniciarem..."
    sleep 5
    
    echo ""
    echo "📊 Status dos containers:"
    $DOCKER_COMPOSE ps
    
    echo ""
    echo "✅ Deploy concluído!"
    echo ""
    echo "📝 Próximos passos:"
    echo "   1. Configure o .env: nano $INSTALL_DIR/.env"
    echo "   2. Reinicie os containers: cd $INSTALL_DIR && docker-compose restart"
    echo "   3. Acesse o dashboard: http://SEU_SERVIDOR:8501"
    echo "   4. Verifique logs: cd $INSTALL_DIR && docker-compose logs -f"
else
    echo ""
    echo "✅ Preparação concluída!"
    echo ""
    echo "📝 Para iniciar manualmente:"
    echo "   cd $INSTALL_DIR"
    echo "   nano .env  # Configure as variáveis"
    echo "   docker-compose up -d"
fi







