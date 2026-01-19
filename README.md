# Notificador IOF MG

Sistema de notificações do Diário Oficial de Minas Gerais que permite configurar buscas por termos específicos e receber notificações por email quando esses termos são encontrados nas publicações.

## Funcionalidades

- 🔍 **Busca por termos**: Configure até 5 termos de busca (com opção de busca exata ou parcial)
- 📧 **Notificações por email**: Receba emails quando seus termos forem encontrados
- 📎 **Anexo CSV**: Opção de receber um arquivo CSV com todos os resultados encontrados
- 🌐 **Interface web**: Interface gráfica para gerenciar configurações de busca
- 🧪 **Backtest**: Teste suas configurações em datas específicas antes de ativar
- 🔎 **Busca FTS5**: Motor de busca full-text otimizado usando SQLite FTS5
- 📄 **API REST**: API RESTful para integração com outros sistemas

## Requisitos

- Python 3.13+
- [UV Python](https://github.com/astral-sh/uv) - Gerenciador de pacotes
- [poppler-utils](https://poppler.freedesktop.org/) - Para extração de texto de PDFs
- (Opcional) Redis - Para processamento assíncrono com RQ
- (Opcional) PostgreSQL - Para produção (SQLite usado por padrão)

### Instalação do poppler-utils

**macOS:**
```bash
brew install poppler
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install poppler-utils
```

## Configuração

### 1. Instalação

```bash
# Clone o repositório (se aplicável)
# cd notificador-iof-mg

# Instale as dependências
uv sync
```

### 2. Configuração do ambiente

1. Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

2. Edite o arquivo `.env` com suas configurações:

#### Configuração de Email

O sistema suporta diferentes provedores de email. Veja exemplos no arquivo `env.example`:

**Gmail (Recomendado):**
```env
MAIL_FROM_ADDRESS=seu-email@gmail.com
MAIL_SMTP_HOST=smtp.gmail.com
MAIL_SMTP_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_SMTP_USER=seu-email@gmail.com
MAIL_SMTP_PASSWORD=sua-senha-de-app
```

> **Importante para Gmail**: Você precisa criar uma "Senha de App" em https://myaccount.google.com/apppasswords. Use essa senha, não sua senha normal do Gmail.

**MailHog (Desenvolvimento local):**
```env
MAIL_SMTP_HOST=localhost
MAIL_SMTP_PORT=1025
MAIL_USE_TLS=false
```

**SendGrid:**
```env
MAIL_SMTP_HOST=smtp.sendgrid.net
MAIL_SMTP_PORT=587
MAIL_USE_TLS=true
MAIL_SMTP_USER=apikey
MAIL_SMTP_PASSWORD=sua-api-key-sendgrid
```

### 3. Banco de Dados

Execute as migrations:
```bash
uv run alembic upgrade head
```

## Executando

### Servidor Web (Interface Gráfica)

```bash
uv run flask run
```

Acesse a interface web em: http://localhost:5000

### Processamento de Diários

O sistema processa diários automaticamente via workers RQ (quando configurado) ou manualmente:

```bash
# Processar diário de uma data específica
uv run python -c "from app.tasks.daily_gazette import process_daily_gazette; from datetime import date; process_daily_gazette(date(2026, 1, 14))"
```

## Como Usar

### Interface Web

1. **Criar Configuração de Busca**:
   - Acesse http://localhost:5000
   - Clique em "Nova Configuração"
   - Preencha:
     - Nome e descrição
     - Termos de busca (até 5 termos)
     - Emails para notificação
     - Opção de anexar CSV
   - Salve a configuração

2. **Testar Configuração (Backtest)**:
   - Na página de detalhes da configuração, clique em "Testar Busca"
   - Selecione uma data
   - O sistema irá:
     - Baixar o diário da data (se necessário)
     - Executar a busca
     - Enviar email de teste (se houver resultados)

3. **Ativar/Desativar**:
   - Use o checkbox "Configuração Ativa" para pausar notificações

### API REST

O sistema também oferece uma API REST para integração:

- `GET /api/search/configs` - Listar configurações
- `POST /api/search/configs` - Criar configuração
- `GET /api/search/configs/<id>` - Obter configuração
- `PUT /api/search/configs/<id>` - Atualizar configuração
- `DELETE /api/search/configs/<id>` - Deletar configuração
- `GET /api/search/configs/<id>/backtest?date=YYYY-MM-DD` - Executar backtest

## Estrutura do Projeto

```
notificador-iof-mg/
├── app/                    # Aplicação Flask
│   ├── api/                # Endpoints REST
│   ├── models/             # Modelos SQLAlchemy
│   ├── services/           # Lógica de negócio
│   ├── tasks/               # Workers (processamento assíncrono)
│   ├── templates/           # Templates HTML (Jinja2)
│   ├── web/                 # Rotas da interface web
│   └── static/              # Arquivos estáticos (CSS, JS)
├── iof/                     # Cliente Diário Oficial
│   ├── v1/                  # API v1 do IOF
│   └── common.py            # Classes compartilhadas
├── search/                  # Motor de busca SQLite FTS5
├── pdf/                     # Extração de texto de PDFs
├── mailer/                  # Sistema de emails
│   ├── csv_generator.py     # Geração de CSV para anexos
│   ├── mailer.py            # Cliente de email
│   └── notification.py      # Templates de notificação
├── migrations/              # Migrations do banco (Alembic)
└── diarios/                 # Banco SQLite com diários processados
```

## Funcionalidades Detalhadas

### Busca de Termos

- **Busca Exata**: Encontra apenas o termo completo exatamente como escrito
- **Busca Parcial**: Encontra o termo mesmo como parte de outras palavras
- Até 5 termos por configuração
- Busca otimizada com SQLite FTS5

### Notificações por Email

- Envio automático quando termos são encontrados
- Até 5 destinatários por configuração
- Assunto customizável
- Link direto para o diário do dia
- Lista de highlights encontrados

### Anexo CSV

Quando a opção "Anexar CSV" está ativada, o email inclui um arquivo CSV com:

- **Data Publicação**: Data do diário oficial
- **Termo**: Termo que foi encontrado
- **Página**: Número da página
- **Conteúdo**: Trecho onde o termo foi encontrado
- **Link**: URL direta para a página

O CSV é formatado com delimitador `;` e codificação UTF-8 com BOM para compatibilidade com Excel.

### Processamento de Diários

O sistema utiliza a **API v1** do Diário Oficial de Minas Gerais:

- Baixa diários automaticamente via API v1
- Extrai texto de PDFs usando poppler-utils
- Indexa conteúdo no banco SQLite FTS5
- Processa buscas de forma otimizada

## Desenvolvimento

Este projeto segue uma abordagem MVP incremental:

- **Fase 1**: SQLite local, interface web básica
- **Fase 2**: Processamento assíncrono com RQ
- **Fase 3**: Migração para PostgreSQL (opcional)
- Cada fase tem checkpoints de teste obrigatórios

### Executar Testes

```bash
# Testes individuais podem ser executados diretamente
uv run python test_script.py
```

## Troubleshooting

### Email não está sendo enviado

1. Verifique as configurações no arquivo `.env`
2. Para Gmail, certifique-se de usar uma "Senha de App"
3. Verifique se `MAIL_USE_TLS=true` para Gmail na porta 587
4. Teste a conexão SMTP usando o backtest na interface web

### Diário não encontrado

- A API v1 pode não ter diários disponíveis para todas as datas
- Verifique se a data é válida e se há diário publicado nessa data
- Algumas datas podem não estar disponíveis na API

### Erro ao processar PDF

- Certifique-se de que `poppler-utils` está instalado
- Verifique se os comandos `pdfinfo` e `pdftotext` estão no PATH

## Licença

Este projeto é um sistema interno para notificações do Diário Oficial de Minas Gerais.