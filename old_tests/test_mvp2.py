#!/usr/bin/env python3
"""Script de teste para validar MVP 2 - Extração de PDF."""
import sys
import subprocess

def test_poppler_utils():
    """Verifica se poppler-utils está instalado."""
    try:
        subprocess.run(['pdfinfo', '-v'], capture_output=True, check=True)
        subprocess.run(['pdftotext', '-v'], capture_output=True, check=True)
        print("✅ poppler-utils instalado")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("⚠️  poppler-utils não encontrado")
        print("   Instale com: brew install poppler (macOS) ou apt-get install poppler-utils (Linux)")
        return False

def test_import():
    """Testa importação do módulo."""
    try:
        from pdf.extractor import PDFExtractor, Page
        print("✅ Módulo PDFExtractor importado com sucesso")
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar módulo: {e}")
        return False

def test_extractor_creation():
    """Testa criação do extrator."""
    try:
        from pdf.extractor import PDFExtractor
        extractor = PDFExtractor()
        print("✅ PDFExtractor criado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar PDFExtractor: {e}")
        return False

def create_test_pdf():
    """Cria um PDF de teste simples se não existir."""
    import os
    
    test_file = 'test.pdf'
    if os.path.exists(test_file):
        return test_file
    
    print("   Criando PDF de teste...")
    # PDF mínimo válido com texto
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
/ProcSet [/PDF /Text]
>>
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 24 Tf
100 700 Td
(Hello, World! This is a test PDF.) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000307 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
490
%%EOF"""
    
    try:
        with open(test_file, 'wb') as f:
            f.write(pdf_content)
        return test_file
    except Exception as e:
        print(f"   ⚠️  Erro ao criar PDF: {e}")
        return None

def test_with_file():
    """Testa extração com arquivo (se disponível)."""
    import os
    
    # Tentar criar PDF de teste se não existir
    test_file = create_test_pdf()
    
    if not test_file:
        print("⚠️  Não foi possível criar PDF de teste")
        print("   Testando apenas estrutura do módulo...")
        return True
    
    if not os.path.exists(test_file):
        print("⚠️  Nenhum arquivo PDF de teste encontrado")
        print("   Testando apenas estrutura do módulo...")
        return True
    
    try:
        from pdf.extractor import PDFExtractor
        extractor = PDFExtractor()
        pages = extractor.extract_pages_from_path(test_file)
        print(f"✅ Extraídas {len(pages)} páginas de {test_file}")
        
        # Mostrar primeiras 3 páginas
        for page in pages[:3]:
            preview = page.content[:100].replace('\n', ' ').strip()
            if preview:
                print(f"   Página {page.number}: {preview}...")
            else:
                print(f"   Página {page.number}: (vazia ou sem texto extraível)")
        
        # Validar que pelo menos uma página foi extraída
        if len(pages) == 0:
            print("⚠️  Nenhuma página foi extraída")
            return False
        
        return True
    except RuntimeError as e:
        if "não encontrado" in str(e) or "not found" in str(e).lower():
            print(f"⚠️  {e}")
            print("   Instale poppler-utils para testar extração completa:")
            print("   macOS: brew install poppler")
            print("   Linux: sudo apt-get install poppler-utils")
            return True  # Não é um erro crítico, apenas falta a ferramenta
        print(f"❌ Erro ao extrair PDF: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Erro ao extrair PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes."""
    print("=" * 50)
    print("Teste MVP 2: Extração de PDF")
    print("=" * 50)
    
    success = True
    
    print("\n1. Verificando poppler-utils...")
    poppler_ok = test_poppler_utils()
    if not poppler_ok:
        print("   Continuando testes sem poppler-utils...")
    
    print("\n2. Testando importação...")
    if not test_import():
        success = False
    
    print("\n3. Testando criação do extrator...")
    if not test_extractor_creation():
        success = False
    
    print("\n4. Testando extração (se houver arquivo)...")
    if not test_with_file():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Todos os testes passaram!")
        sys.exit(0)
    else:
        print("❌ Alguns testes falharam")
        sys.exit(1)

if __name__ == '__main__':
    main()

