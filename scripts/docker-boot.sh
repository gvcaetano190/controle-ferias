#!/bin/bash
# ===========================================
# Script para configurar inicialização automática no boot
# Compatível com: Linux Ubuntu
# ===========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "⚙️  Configurando inicialização automática no boot..."
echo ""

# Verifica se é Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "⚠️  Este script é apenas para Linux Ubuntu."
    echo "   No macOS, configure o Docker Desktop para iniciar automaticamente nas Preferências."
    exit 1
fi

# Verifica se está rodando como root para algumas operações
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Algumas operações precisam de sudo."
fi

echo "1️⃣ Habilitando Docker para iniciar no boot..."
sudo systemctl enable docker
sudo systemctl enable containerd
echo "   ✅ Docker habilitado para iniciar no boot"
echo ""

echo "2️⃣ Configurando docker-compose para iniciar containers no boot..."
# Remove entrada antiga se existir
(crontab -l 2>/dev/null | grep -v "docker-compose up -d") | crontab - 2>/dev/null || true

# Adiciona nova entrada (inicia 2 minutos após boot)
(crontab -l 2>/dev/null; echo "@reboot sleep 120 && cd $PROJECT_DIR && docker-compose up -d >> $PROJECT_DIR/logs/docker-boot.log 2>&1") | crontab -
echo "   ✅ Adicionado ao crontab"
echo ""

echo "✅ Configuração concluída!"
echo ""
echo "📝 O sistema iniciará automaticamente 2 minutos após o boot."
echo "   Logs em: $PROJECT_DIR/logs/docker-boot.log"
echo ""
echo "💡 Para testar, reinicie o sistema ou execute:"
echo "   sudo systemctl reboot"
echo ""

