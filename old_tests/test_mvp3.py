#!/usr/bin/env python3
"""Script de teste para validar MVP 3 - Motor de Busca SQLite FTS5."""
import sys
import os
from datetime import date
from dataclasses import dataclass

def test_import():
    """Testa importação do módulo."""
    try:
        from search.source import SearchSource, Term, Trigger, Report, Highlight, Pagina
        print("✅ Módulos importados com sucesso")
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar módulos: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_source_creation():
    """Testa criação do SearchSource."""
    try:
        from search.source import SearchSource
        
        # Usar banco de teste
        db_path = 'search_test.db'
        if os.path.exists(db_path):
            os.remove(db_path)
        
        source = SearchSource(db_path)
        print(f"✅ SearchSource criado: {db_path}")
        source.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao criar SearchSource: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_pages():
    """Testa importação de páginas."""
    try:
        from search.source import SearchSource, Pagina
        
        db_path = 'search_test.db'
        if os.path.exists(db_path):
            os.remove(db_path)
        
        source = SearchSource(db_path)
        
        # Criar páginas de teste
        @dataclass
        class PaginaTest:
            titulo: str
            num_pagina: int
            descricao: str
            conteudo: str
            data_publicacao: date
        
        pages = [
            PaginaTest(
                titulo="Página 1",
                num_pagina=1,
                descricao="",
                conteudo="Este é um texto de teste com a palavra MASP mencionada aqui.",
                data_publicacao=date.today()
            ),
            PaginaTest(
                titulo="Página 2",
                num_pagina=2,
                descricao="",
                conteudo="Outro texto sem a palavra buscada.",
                data_publicacao=date.today()
            )
        ]
        
        # Converter para Pagina
        paginas = [
            Pagina(
                titulo=p.titulo,
                num_pagina=p.num_pagina,
                descricao=p.descricao,
                conteudo=p.conteudo,
                data_publicacao=p.data_publicacao
            )
            for p in pages
        ]
        
        source.import_pages(paginas)
        print(f"✅ Importadas {len(paginas)} páginas")
        
        source.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao importar páginas: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_search():
    """Testa busca."""
    try:
        from search.source import SearchSource, Term, Trigger
        
        db_path = 'search_test.db'
        if not os.path.exists(db_path):
            print("⚠️  Banco de teste não existe, criando...")
            test_import_pages()
        
        source = SearchSource(db_path)
        
        # Buscar termo
        terms = [Term(term="MASP", exact=False)]
        report = source.lookup(Trigger.CRON, date.today(), terms)
        
        print(f"✅ Busca encontrou {report.count} resultados")
        for highlight in report.highlights:
            print(f"   Página {highlight.page}: {highlight.content[:50]}...")
        
        source.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao buscar: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_has_pages():
    """Testa verificação de páginas."""
    try:
        from search.source import SearchSource
        
        db_path = 'search_test.db'
        if not os.path.exists(db_path):
            print("⚠️  Banco de teste não existe")
            return False
        
        source = SearchSource(db_path)
        has = source.has_pages(date.today())
        print(f"✅ has_pages({date.today()}): {has}")
        
        source.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar páginas: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes."""
    print("=" * 50)
    print("Teste MVP 3: Motor de Busca SQLite FTS5")
    print("=" * 50)
    
    success = True
    
    print("\n1. Testando importação...")
    if not test_import():
        success = False
    
    print("\n2. Testando criação do SearchSource...")
    if not test_source_creation():
        success = False
    
    print("\n3. Testando importação de páginas...")
    if not test_import_pages():
        success = False
    
    print("\n4. Testando busca...")
    if not test_search():
        success = False
    
    print("\n5. Testando has_pages...")
    if not test_has_pages():
        success = False
    
    # Verificar banco
    db_path = 'search_test.db'
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"\n✅ Banco de dados existe: {db_path} ({size} bytes)")
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Todos os testes passaram!")
        sys.exit(0)
    else:
        print("❌ Alguns testes falharam")
        sys.exit(1)

if __name__ == '__main__':
    main()

