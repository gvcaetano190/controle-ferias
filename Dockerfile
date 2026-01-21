FROM python:3.11-slim

# Metadados
LABEL maintainer="Sistema de Controle de Férias"
LABEL description="Sistema de gerenciamento de férias com Streamlit e scheduler"

# Define diretório de trabalho
WORKDIR /app

# Configura timezone para São Paulo (Brasil)
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instala dependências do sistema (incluindo WeasyPrint)
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    procps \
    tzdata \
    # Dependências do WeasyPrint para geração de PDF
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivos de dependências primeiro (cache de layers)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia todo o código
COPY . .

# Torna scripts executáveis
RUN chmod +x scripts/*.sh

# Cria diretórios necessários
RUN mkdir -p data/cache download logs

# Expõe porta do Streamlit
EXPOSE 8501

# Comando padrão (pode ser sobrescrito no docker-compose)
CMD ["./scripts/iniciar.sh"]

