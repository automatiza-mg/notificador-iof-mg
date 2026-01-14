#!/usr/bin/env python3
"""Script para testar quais datas funcionam na API v1 sem autenticação."""
import sys
import requests
from datetime import date, timedelta

def test_api_v1_date(test_date: date) -> tuple[bool, str]:
    """Testa se uma data funciona na API v1."""
    try:
        url = (
            "https://www.jornalminasgerais.mg.gov.br/api/v1/"
            f"Jornal/ObterEdicaoPorDataPublicacao"
            f"?dataPublicacao={test_date.strftime('%Y-%m-%d')}"
        )
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data and 'dados' in data:
                dados = data.get('dados', {})
                arquivo = dados.get('arquivoCadernoPrincipal', {})
                if arquivo and arquivo.get('arquivo'):
                    size = len(arquivo['arquivo'])
                    pages = arquivo.get('totalPaginas', 'N/A')
                    return True, f"✅ Funciona! PDF: {size:,} chars, {pages} páginas"
                else:
                    return False, "⚠️  Resposta sem arquivo"
            else:
                return False, "⚠️  Resposta sem dados"
        elif response.status_code == 401:
            return False, "❌ 401 Unauthorized (requer autenticação)"
        elif response.status_code == 404:
            return False, "⚠️  404 Not Found (diário não existe)"
        else:
            return False, f"❌ Status {response.status_code}"
    except Exception as e:
        return False, f"❌ Erro: {str(e)[:50]}"

def test_multiple_dates():
    """Testa múltiplas datas para encontrar quais funcionam."""
    print("="*70)
    print("TESTE: API v1 - Quais datas funcionam sem autenticação?")
    print("="*70)
    
    # Testar últimas 30 dias
    results = []
    working_dates = []
    
    print("\nTestando últimas 30 dias...")
    for i in range(30):
        test_date = date.today() - timedelta(days=i)
        success, message = test_api_v1_date(test_date)
        results.append((test_date, success, message))
        
        if success:
            working_dates.append(test_date)
            print(f"  {test_date.strftime('%Y-%m-%d')}: {message}")
        else:
            if i < 10:  # Mostrar apenas primeiros 10 erros
                print(f"  {test_date.strftime('%Y-%m-%d')}: {message}")
    
    print(f"\n{'='*70}")
    print(f"RESUMO: {len(working_dates)} datas funcionam de {len(results)} testadas")
    
    if working_dates:
        print(f"\n✅ Datas que funcionam:")
        for d in working_dates[:10]:  # Mostrar até 10
            print(f"   - {d.strftime('%Y-%m-%d')}")
        if len(working_dates) > 10:
            print(f"   ... e mais {len(working_dates) - 10} datas")
    else:
        print("\n❌ Nenhuma data funcionou sem autenticação")
    
    return working_dates

def test_backtest_new_date(new_date: date):
    """Testa backtest com uma data nova (que não está no banco)."""
    print("\n" + "="*70)
    print(f"TESTE: Backtest com data NOVA ({new_date.strftime('%Y-%m-%d')})")
    print("="*70)
    
    try:
        import requests
        
        # Primeiro, verificar se tem configuração
        response = requests.get("http://localhost:5000/api/search/configs")
        if response.status_code != 200:
            print("❌ Erro ao buscar configurações")
            return False
        
        configs = response.json()
        if not configs:
            print("❌ Nenhuma configuração encontrada. Crie uma primeiro.")
            return False
        
        config_id = configs[0]['id']
        print(f"✅ Usando configuração ID: {config_id}")
        
        # Testar backtest
        url = f"http://localhost:5000/api/search/configs/{config_id}/backtest?date={new_date.strftime('%Y-%m-%d')}"
        print(f"\nExecutando: GET {url}")
        
        response = requests.get(url, timeout=120)  # Timeout maior para processar PDF
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backtest funcionou!")
            print(f"   Encontrados: {data.get('count', 0)} resultados")
            print(f"   Data: {data.get('publish_date')}")
            print(f"   Termos: {[t['term'] for t in data.get('search_terms', [])]}")
            return True
        elif response.status_code == 404:
            error_data = response.json()
            print(f"❌ Erro 404: {error_data.get('message', 'Não encontrado')}")
            return False
        elif response.status_code == 500:
            error_data = response.json()
            print(f"❌ Erro 500: {error_data.get('message', 'Erro interno')}")
            # Pode ser que a API v1 retornou 401
            if '401' in str(error_data) or 'autenticação' in str(error_data).lower():
                print("   ⚠️  Provavelmente a API v1 requer autenticação para esta data")
            return False
        else:
            print(f"❌ Status inesperado: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Servidor Flask não está rodando!")
        print("   Execute: uv run python run.py")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes."""
    print("="*70)
    print("TESTE COMPLETO: API v1 e Backtest")
    print("="*70)
    
    # Teste 1: Encontrar datas que funcionam
    working_dates = test_multiple_dates()
    
    # Teste 2: Testar backtest com data nova
    if working_dates:
        # Usar a primeira data que funciona (mais recente)
        new_date = working_dates[0]
        print(f"\n{'='*70}")
        print(f"Usando data: {new_date.strftime('%Y-%m-%d')} (mais recente que funciona)")
    else:
        # Se nenhuma funcionou, tentar com data de hoje
        new_date = date.today()
        print(f"\n{'='*70}")
        print(f"Nenhuma data funcionou. Tentando com data de hoje: {new_date.strftime('%Y-%m-%d')}")
    
    # Verificar se a data já está no banco
    import os
    db_path = "diarios/diarios.db"
    if os.path.exists(db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM documentos WHERE data_publicacao = ?",
            (new_date.strftime('%Y-%m-%d'),)
        )
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"\n⚠️  ATENÇÃO: Esta data já tem {count} páginas no banco!")
            print("   O backtest vai usar dados do banco, não vai baixar da API.")
            print("   Para testar download real, use uma data que não está no banco.")
            
            # Tentar encontrar uma data que funciona mas não está no banco
            for test_date in working_dates[:10]:
                cursor.execute(
                    "SELECT COUNT(*) FROM documentos WHERE data_publicacao = ?",
                    (test_date.strftime('%Y-%m-%d'),)
                )
                count = cursor.fetchone()[0]
                if count == 0:
                    new_date = test_date
                    print(f"\n✅ Usando data alternativa: {new_date.strftime('%Y-%m-%d')} (não está no banco)")
                    break
        
        conn.close()
    
    success = test_backtest_new_date(new_date)
    
    # Resumo final
    print("\n" + "="*70)
    print("RESUMO FINAL")
    print("="*70)
    print(f"✅ Datas que funcionam na API v1: {len(working_dates)}")
    print(f"{'✅' if success else '❌'} Backtest com data nova: {'Funcionou' if success else 'Falhou'}")
    
    if not working_dates:
        print("\n⚠️  CONCLUSÃO: A API v1 parece requerer autenticação para todas as datas testadas.")
        print("   Você precisará de credenciais IOF para usar o sistema completamente.")
    elif success:
        print("\n✅ CONCLUSÃO: O sistema funciona! Algumas datas funcionam sem autenticação.")
    else:
        print("\n⚠️  CONCLUSÃO: Algumas datas funcionam na API v1, mas o backtest falhou.")
        print("   Pode ser problema de processamento ou a data específica requer autenticação.")
    
    sys.exit(0 if (working_dates and success) else 1)

if __name__ == '__main__':
    main()
