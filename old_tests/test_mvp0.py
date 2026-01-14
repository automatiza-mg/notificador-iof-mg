#!/usr/bin/env python3
"""Script de teste para validar MVP 0 - Setup Inicial."""
import sys

def test_imports():
    """Testa se os módulos podem ser importados."""
    try:
        import flask
        print(f"✅ Flask {flask.__version__} instalado")
    except ImportError as e:
        print(f"❌ Erro ao importar Flask: {e}")
        return False
    
    try:
        from app import create_app
        print("✅ app.create_app importado com sucesso")
    except ImportError as e:
        print(f"❌ Erro ao importar create_app: {e}")
        return False
    
    return True

def test_app_creation():
    """Testa se a aplicação pode ser criada."""
    try:
        from app import create_app
        app = create_app()
        env = app.config.get('APP_ENV', 'development')
        print(f"✅ App criado com sucesso (ambiente: {env})")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar app: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes."""
    print("=" * 50)
    print("Teste MVP 0: Setup Inicial")
    print("=" * 50)
    
    success = True
    
    print("\n1. Testando imports...")
    if not test_imports():
        success = False
    
    print("\n2. Testando criação da app...")
    if not test_app_creation():
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

