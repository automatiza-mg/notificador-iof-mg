#!/usr/bin/env python3
"""Script para baixar jornal da API v1 e salvar localmente."""
import sys
import json
import base64
import os
from datetime import date
from pathlib import Path

def download_journal_save_locally(target_date: date):
    """Baixa jornal da API v1 e salva localmente."""
    print("="*70)
    print(f"BAIXANDO E SALVANDO JORNAL: {target_date.strftime('%Y-%m-%d')}")
    print("="*70)
    
    # Criar diretório para salvar
    output_dir = Path("jornal_downloaded")
    output_dir.mkdir(exist_ok=True)
    print(f"\n📁 Diretório de saída: {output_dir.absolute()}")
    
    # Passo 1: Acessar API v1
    print("\n" + "-"*70)
    print("PASSO 1: Acessando API v1")
    print("-"*70)
    
    import requests
    url = (
        "https://www.jornalminasgerais.mg.gov.br/api/v1/"
        f"Jornal/ObterEdicaoPorDataPublicacao"
        f"?dataPublicacao={target_date.strftime('%Y-%m-%d')}"
    )
    
    print(f"URL: {url}")
    print("Fazendo requisição...")
    
    response = requests.get(url, timeout=60)
    
    if response.status_code != 200:
        print(f"❌ Erro: Status {response.status_code}")
        return False
    
    print(f"✅ Resposta recebida: {response.status_code}")
    
    # Passo 2: Parsear JSON
    print("\n" + "-"*70)
    print("PASSO 2: Parseando resposta JSON")
    print("-"*70)
    
    data = response.json()
    
    # Salvar JSON completo
    json_file = output_dir / f"resposta_api_{target_date.strftime('%Y-%m-%d')}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    json_size = os.path.getsize(json_file)
    print(f"✅ JSON salvo: {json_file.name} ({json_size:,} bytes)")
    
    # Passo 3: Extrair Base64
    print("\n" + "-"*70)
    print("PASSO 3: Extraindo PDF em Base64")
    print("-"*70)
    
    dados = data.get('dados', {})
    arquivo_data = dados.get('arquivoCadernoPrincipal', {})
    
    if not arquivo_data:
        print("❌ Resposta não contém arquivoCadernoPrincipal")
        return False
    
    arquivo_base64 = arquivo_data.get('arquivo', '')
    total_paginas = arquivo_data.get('totalPaginas', 0)
    
    if not arquivo_base64:
        print("❌ Campo 'arquivo' está vazio")
        return False
    
    base64_size = len(arquivo_base64)
    print(f"✅ Base64 encontrado: {base64_size:,} caracteres")
    print(f"   Total de páginas: {total_paginas}")
    print(f"   Primeiros 100 chars: {arquivo_base64[:100]}...")
    
    # Salvar Base64 em arquivo texto
    base64_file = output_dir / f"pdf_base64_{target_date.strftime('%Y-%m-%d')}.txt"
    with open(base64_file, 'w', encoding='utf-8') as f:
        f.write(arquivo_base64)
    
    print(f"✅ Base64 salvo: {base64_file.name}")
    
    # Passo 4: Decodificar Base64 para PDF
    print("\n" + "-"*70)
    print("PASSO 4: Decodificando Base64 para PDF")
    print("-"*70)
    
    try:
        pdf_bytes = base64.b64decode(arquivo_base64)
        pdf_size = len(pdf_bytes)
        print(f"✅ PDF decodificado: {pdf_size:,} bytes ({pdf_size / (1024*1024):.2f} MB)")
    except Exception as e:
        print(f"❌ Erro ao decodificar Base64: {e}")
        return False
    
    # Salvar PDF
    pdf_file = output_dir / f"jornal_{target_date.strftime('%Y-%m-%d')}.pdf"
    with open(pdf_file, 'wb') as f:
        f.write(pdf_bytes)
    
    print(f"✅ PDF salvo: {pdf_file.name}")
    
    # Passo 5: Extrair texto do PDF
    print("\n" + "-"*70)
    print("PASSO 5: Extraindo texto do PDF")
    print("-"*70)
    
    try:
        from pdf.extractor import PDFExtractor
        extractor = PDFExtractor()
        pages = extractor.extract_pages(pdf_bytes)
        
        print(f"✅ Extraídas {len(pages)} páginas")
        
        # Salvar texto de cada página
        texto_dir = output_dir / "texto_extraido"
        texto_dir.mkdir(exist_ok=True)
        
        for page in pages:
            page_file = texto_dir / f"pagina_{page.number:03d}.txt"
            with open(page_file, 'w', encoding='utf-8') as f:
                f.write(page.content)
        
        print(f"✅ Texto salvo em: {texto_dir.name}/")
        print(f"   {len(pages)} arquivos criados (pagina_001.txt, pagina_002.txt, ...)")
        
        # Salvar resumo
        resumo_file = output_dir / f"resumo_{target_date.strftime('%Y-%m-%d')}.txt"
        with open(resumo_file, 'w', encoding='utf-8') as f:
            f.write(f"Jornal do Diário Oficial de MG\n")
            f.write(f"Data: {target_date.strftime('%Y-%m-%d')}\n")
            f.write(f"Total de páginas: {len(pages)}\n")
            f.write(f"Tamanho do PDF: {pdf_size:,} bytes ({pdf_size / (1024*1024):.2f} MB)\n")
            f.write(f"Tamanho do Base64: {base64_size:,} caracteres\n")
            f.write(f"\n{'='*70}\n")
            f.write(f"PRIMEIRAS 3 PÁGINAS (amostra):\n")
            f.write(f"{'='*70}\n\n")
            
            for page in pages[:3]:
                f.write(f"\n--- PÁGINA {page.number} ---\n")
                f.write(page.content[:500])
                f.write("\n...\n")
        
        print(f"✅ Resumo salvo: {resumo_file.name}")
        
    except Exception as e:
        print(f"⚠️  Erro ao extrair texto (pode ser que poppler não esteja instalado): {e}")
        print("   PDF foi salvo, mas texto não foi extraído")
    
    # Resumo final
    print("\n" + "="*70)
    print("RESUMO - ARQUIVOS SALVOS")
    print("="*70)
    print(f"📁 Diretório: {output_dir.absolute()}")
    print(f"\nArquivos criados:")
    print(f"  1. {json_file.name} - Resposta completa da API (JSON)")
    print(f"  2. {base64_file.name} - PDF em Base64 (texto)")
    print(f"  3. {pdf_file.name} - PDF decodificado (binário)")
    if 'pages' in locals():
        print(f"  4. {texto_dir.name}/ - {len(pages)} arquivos de texto extraído")
        print(f"  5. {resumo_file.name} - Resumo e amostras")
    
    print(f"\n📊 Tamanhos:")
    print(f"   JSON: {json_size:,} bytes")
    print(f"   Base64: {base64_size:,} caracteres")
    print(f"   PDF: {pdf_size:,} bytes ({pdf_size / (1024*1024):.2f} MB)")
    
    return True

def main():
    """Executa o download."""
    target_date = date(2026, 1, 9)
    
    success = download_journal_save_locally(target_date)
    
    if success:
        print("\n✅ Download e salvamento concluídos com sucesso!")
        print(f"\n💡 Dica: Explore os arquivos em: jornal_downloaded/")
        sys.exit(0)
    else:
        print("\n❌ Falha no download")
        sys.exit(1)

if __name__ == '__main__':
    main()
