#!/usr/bin/env python3
"""Script para criar um PDF de teste simples."""
import sys

def create_simple_pdf(filename: str = "test.pdf"):
    """
    Cria um PDF simples de teste usando apenas Python (sem dependências externas).
    Este é um PDF mínimo válido com uma página contendo texto.
    """
    # PDF mínimo válido com "Hello, World!" na página
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
        with open(filename, 'wb') as f:
            f.write(pdf_content)
        print(f"✅ PDF de teste criado: {filename}")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar PDF: {e}")
        return False

if __name__ == '__main__':
    filename = sys.argv[1] if len(sys.argv) > 1 else "test.pdf"
    success = create_simple_pdf(filename)
    sys.exit(0 if success else 1)
