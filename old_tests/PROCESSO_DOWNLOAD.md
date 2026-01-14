# Processo de Download do Diário Oficial

## ✅ Confirmação: A API retorna Base64

Sim! A API v1 retorna o PDF **codificado em Base64** dentro de um JSON.

## 📋 Processo Completo (Passo a Passo)

### 1. Requisição à API v1

```
GET https://www.jornalminasgerais.mg.gov.br/api/v1/Jornal/ObterEdicaoPorDataPublicacao?dataPublicacao=2026-01-09
```

**Resposta:** JSON com estrutura:
```json
{
  "dados": {
    "dataPublicacao": "2026-01-09",
    "arquivoCadernoPrincipal": {
      "arquivo": "MIAGCSqGSIb3DQEHAqCAMIACAQExDzANBglghkgBZQMEAgEFADCABgkqhkiG9w0BBwGggASDIxkhJVBERi0xLjcKJYGBgYEKCjIg...",  // ⭐ PDF em Base64
      "totalPaginas": 48,
      "arquivoUnico": true,
      ...
    }
  }
}
```

### 2. Extração do Base64

- Campo: `dados.arquivoCadernoPrincipal.arquivo`
- Tamanho: **3.080.044 caracteres** (para 2026-01-09)
- Formato: String Base64

### 3. Decodificação Base64 → PDF

```python
pdf_bytes = base64.b64decode(arquivo_base64)
```

**Resultado:**
- PDF binário: **2.310.032 bytes** (2.20 MB)
- 48 páginas

### 4. Extração de Texto

Usando `poppler-utils` (pdfinfo + pdftotext):
- Extrai texto de cada página
- Salva em arquivos separados

### 5. Importação no Banco FTS5

- Texto importado no SQLite
- Índice FTS5 criado automaticamente
- Pronto para busca

## 📁 Arquivos Salvos (jornal_downloaded/)

### Estrutura Criada:

```
jornal_downloaded/
├── resposta_api_2026-01-09.json      (2.9 MB) - Resposta completa da API
├── pdf_base64_2026-01-09.txt         (2.9 MB) - PDF em Base64 (texto puro)
├── jornal_2026-01-09.pdf              (2.2 MB) - PDF decodificado (pode abrir no leitor)
├── resumo_2026-01-09.txt              (1.9 KB) - Resumo e amostras
└── texto_extraido/
    ├── pagina_001.txt                 (14 KB) - Texto da página 1
    ├── pagina_002.txt                 (17 KB) - Texto da página 2
    ├── pagina_003.txt                 (22 KB) - Texto da página 3
    └── ... (48 arquivos no total)
```

## 📊 Comparação de Tamanhos

| Formato | Tamanho | Observação |
|---------|---------|------------|
| **Base64** | 3.080.044 chars | ~33% maior que PDF (codificação) |
| **PDF** | 2.310.032 bytes | Arquivo binário original |
| **JSON** | 3.083.131 bytes | JSON completo com Base64 + metadados |
| **Texto extraído** | ~1 MB total | 48 arquivos de texto |

## 🔍 O que você pode fazer agora

1. **Abrir o PDF:**
   ```bash
   open jornal_downloaded/jornal_2026-01-09.pdf
   ```

2. **Ver texto extraído:**
   ```bash
   cat jornal_downloaded/texto_extraido/pagina_001.txt
   ```

3. **Ver resumo:**
   ```bash
   cat jornal_downloaded/resumo_2026-01-09.txt
   ```

4. **Ver Base64:**
   ```bash
   head -c 200 jornal_downloaded/pdf_base64_2026-01-09.txt
   ```

## 💡 Por que Base64?

Base64 é usado para:
- **Transmitir dados binários via JSON** (JSON só aceita texto)
- **Enviar PDFs via APIs REST**
- **Evitar problemas de encoding** em requisições HTTP

**Fórmula:** Base64 ≈ PDF × 1.33 (aproximadamente 33% maior)

## 🔄 Fluxo Completo no Sistema

```
1. API v1 retorna JSON com PDF em Base64
   ↓
2. Sistema decodifica Base64 → PDF binário
   ↓
3. Extrai texto de cada página (poppler-utils)
   ↓
4. Importa texto no banco SQLite FTS5
   ↓
5. Busca termos configurados
   ↓
6. Retorna resultados formatados
```

## ✅ Confirmações

- ✅ API v1 retorna PDF em Base64
- ✅ Base64 pode ser decodificado para PDF
- ✅ PDF pode ser extraído para texto
- ✅ Texto pode ser importado no banco
- ✅ Sistema funciona sem credenciais para muitas datas
