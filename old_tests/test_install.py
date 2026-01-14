#!/usr/bin/env python3
"""Script simples para testar se a instalação está funcionando."""
import sys

def test_imports():
    """Testa se todos os módulos podem ser importados."""
    errors = []
    
    try:
        import flask
        print(f"✅ Flask {flask.__version__}")
    except ImportError as e:
        errors.append(f"Flask: {e}")
        print(f"❌ Flask: {e}")
    
    try:
        from app import create_app
        print("✅ app.create_app")
    except ImportError as e:
        errors.append(f"app: {e}")
        print(f"❌ app: {e}")
    
    try:
        from app.models.search_config import SearchConfig
        print("✅ app.models")
    except ImportError as e:
        errors.append(f"app.models: {e}")
        print(f"❌ app.models: {e}")
    
    try:
        from pdf.extractor import PDFExtractor
        print("✅ pdf.extractor")
    except ImportError as e:
        errors.append(f"pdf: {e}")
        print(f"❌ pdf: {e}")
    
    try:
        from search.source import SearchSource
        print("✅ search.source")
    except ImportError as e:
        errors.append(f"search: {e}")
        print(f"❌ search: {e}")
    
    try:
        from iof.client import IOFClient
        print("✅ iof.client")
    except ImportError as e:
        errors.append(f"iof: {e}")
        print(f"❌ iof: {e}")
    
    try:
        from mailer.mailer import Mailer
        print("✅ mailer.mailer")
    except ImportError as e:
        errors.append(f"mailer: {e}")
        print(f"❌ mailer: {e}")
    
    return len(errors) == 0

def test_app_creation():
    """Testa criação da aplicação."""
    try:
        from app import create_app
        app = create_app()
        print(f"✅ App criada (ambiente: {app.config.get('APP_ENV', 'development')})")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar app: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("Teste de Instalação - Notificador IOF MG")
    print("=" * 60)
    
    print("\n1. Testando imports...")
    imports_ok = test_imports()
    
    print("\n2. Testando criação da app...")
    app_ok = test_app_creation()
    
    print("\n" + "=" * 60)
    if imports_ok and app_ok:
        print("✅ Todos os testes passaram!")
        print("\nPróximos passos:")
        print("1. Configure o arquivo .env (copie de env.example)")
        print("2. Execute: uv run python test_mvp1.py")
        print("3. Execute: uv run python run.py")
        sys.exit(0)
    else:
        print("❌ Alguns testes falharam")
        print("\nVerifique se:")
        print("1. Executou: uv sync")
        print("2. Todos os pacotes foram instalados corretamente")
        sys.exit(1)

if __name__ == '__main__':
    main()
