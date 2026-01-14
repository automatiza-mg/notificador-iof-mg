#!/usr/bin/env python3
"""Script de teste para validar MVP 1 - Modelos SQLAlchemy."""
import sys
import os

def test_models():
    """Testa criação de modelos e inserção manual de dados."""
    try:
        from app import create_app
        from app.extensions import db
        from app.models.search_config import SearchConfig, SearchTerm
        
        app = create_app()
        
        # Usar banco em memória para teste (mais limpo)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            # Limpar e criar tabelas
            db.drop_all()
            db.create_all()
            print("✅ Tabelas criadas")
            
            # Criar configuração
            config = SearchConfig(
                label="Teste",
                description="Configuração de teste",
                attach_csv=False,
                mail_to=["teste1@example.com", "teste2@example.com"],  # Testar lista
                mail_subject="Teste",
                active=True
            )
            db.session.add(config)
            db.session.commit()
            print(f"✅ Config criada: ID={config.id}")
            print(f"   mail_to: {config.mail_to}")  # Verificar se lista foi salva corretamente
            
            # Criar termo
            term = SearchTerm(term="teste", exact=True, search_config_id=config.id)
            db.session.add(term)
            db.session.commit()
            print(f"✅ Termo criado: {term.term}")
            
            # Buscar e verificar se mail_to foi salvo corretamente
            found = SearchConfig.query.first()
            if found:
                print(f"✅ Config encontrada: {found.label}")
                print(f"   Termos: {[t.term for t in found.terms]}")
                print(f"   mail_to (após busca): {found.mail_to} (tipo: {type(found.mail_to).__name__})")
                # Verificar se mail_to é uma lista
                if not isinstance(found.mail_to, list):
                    print(f"❌ mail_to deveria ser lista, mas é {type(found.mail_to)}")
                    return False
                if len(found.mail_to) != 2:
                    print(f"❌ mail_to deveria ter 2 itens, mas tem {len(found.mail_to)}")
                    return False
            else:
                print("❌ Config não encontrada")
                return False
            
            # Verificar banco (apenas se não for em memória)
            db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if 'sqlite' in db_path and ':memory:' not in db_path:
                db_file = db_path.replace('sqlite:///', '')
                if os.path.exists(db_file):
                    size = os.path.getsize(db_file)
                    print(f"✅ Banco de dados existe: {db_file} ({size} bytes)")
                else:
                    print(f"⚠️  Arquivo de banco não encontrado: {db_file}")
            elif ':memory:' in db_path:
                print("✅ Banco em memória (temporário para testes)")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes."""
    print("=" * 50)
    print("Teste MVP 1: Modelos SQLAlchemy")
    print("=" * 50)
    
    success = test_models()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Todos os testes passaram!")
        sys.exit(0)
    else:
        print("❌ Alguns testes falharam")
        sys.exit(1)

if __name__ == '__main__':
    main()

