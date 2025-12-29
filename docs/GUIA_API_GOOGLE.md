# 🔑 Guia Rápido: Configurar Google Sheets API para Múltiplas Abas

Para ler **todas as abas** da sua planilha do Google Sheets (DEZEMBRO 2024, JANEIRO 2025, etc.), você precisa configurar a API do Google.

---

## ⚡ Método Rápido (5 minutos)

### Passo 1: Criar Projeto no Google Cloud

1. Acesse: https://console.cloud.google.com/
2. Clique em **"Criar Projeto"** (ou selecione um existente)
3. Dê um nome: `controle-ferias` (ou outro)
4. Clique em **"Criar"**

### Passo 2: Ativar Google Sheets API

1. No menu lateral, vá em **"APIs e Serviços"** > **"Biblioteca"**
2. Procure por **"Google Sheets API"**
3. Clique em **"Ativar"**

### Passo 3: Criar Conta de Serviço

1. Vá em **"APIs e Serviços"** > **"Credenciais"**
2. Clique em **"Criar credenciais"** > **"Conta de serviço"**
3. Dê um nome: `controle-ferias-service`
4. Clique em **"Criar e continuar"**
5. Pule as permissões (clique em **"Concluir"**)

### Passo 4: Baixar Chave JSON

1. Na lista de contas de serviço, clique na que você criou
2. Vá na aba **"Chaves"**
3. Clique em **"Adicionar chave"** > **"Criar nova chave"**
4. Escolha **"JSON"**
5. Clique em **"Criar"**
6. O arquivo JSON será baixado automaticamente (guarde em local seguro!)

### Passo 5: Compartilhar Planilha com a Conta de Serviço

1. Abra o arquivo JSON baixado
2. Procure por `"client_email"` (exemplo: `controle-ferias-service@seu-projeto.iam.gserviceaccount.com`)
3. Abra sua planilha no Google Sheets
4. Clique em **"Compartilhar"** (botão no canto superior direito)
5. Cole o email da conta de serviço
6. Dê permissão **"Visualizador"**
7. Clique em **"Enviar"**

### Passo 6: Usar no Streamlit

1. No Streamlit, marque **"Usar Google Sheets API"**
2. Clique em **"Browse files"** e selecione o arquivo JSON baixado
3. Cole a URL da planilha
4. Clique em **"Carregar Planilha"**
5. ✅ Todas as abas serão carregadas!

---

## 📋 Resumo dos Passos

```
1. Google Cloud Console → Criar Projeto
2. Ativar Google Sheets API
3. Criar Conta de Serviço
4. Baixar Chave JSON
5. Compartilhar planilha com email da conta de serviço
6. Fazer upload do JSON no Streamlit
```

---

## ❓ Dúvidas Frequentes

### Quanto custa?
**Grátis!** A Google Sheets API tem um limite generoso gratuito (várias requisições por minuto).

### É seguro?
Sim! A conta de serviço só tem acesso à planilha que você compartilhar com ela. Ninguém mais pode acessar.

### Preciso fazer isso toda vez?
**Não!** Depois de configurado uma vez, você só precisa fazer upload do JSON no Streamlit sempre que usar.

### Funciona offline?
Não, precisa de internet para acessar o Google Sheets.

---

## 🔗 Links Úteis

- [Google Cloud Console](https://console.cloud.google.com/)
- [Documentação Google Sheets API](https://developers.google.com/sheets/api)
- [Documentação gspread](https://docs.gspread.org/)

---

**Tempo estimado:** 5 minutos  
**Dificuldade:** ⭐⭐ Fácil

