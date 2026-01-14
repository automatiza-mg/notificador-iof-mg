#!/usr/bin/env python3
"""Script para testar métodos de acesso ao Diário Oficial sem credenciais."""
import sys
import requests
from datetime import date, timedelta

def print_test(name: str):
    """Imprime cabeçalho de teste."""
    print(f"\n{'='*60}")
    print(f"TESTE: {name}")
    print('='*60)

def print_result(success: bool, message: str = ""):
    """Imprime resultado do teste."""
    status = "✅ PASSOU" if success else "❌ FALHOU"
    print(f"{status}: {message}")

def test_api_v1():
    """Teste 1: API v1 - ObterEdicaoPorDataPublicacao."""
    print_test("API v1 - ObterEdicaoPorDataPublicacao")
    
    # Testar com uma data recente (últimos 7 dias)
    test_dates = []
    for i in range(7):
        test_date = date.today() - timedelta(days=i)
        test_dates.append(test_date)
    
    success_count = 0
    for test_date in test_dates:
        try:
            url = (
                "https://www.jornalminasgerais.mg.gov.br/api/v1/"
                f"Jornal/ObterEdicaoPorDataPublicacao"
                f"?dataPublicacao={test_date.strftime('%Y-%m-%d')}"
            )
            
            print(f"\n  Testando data: {test_date.strftime('%Y-%m-%d')}")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data and 'dados' in data:
                    dados = data.get('dados', {})
                    if dados:
                        arquivo = dados.get('arquivoCadernoPrincipal', {})
                        
                        if arquivo and arquivo.get('arquivo'):
                            print_result(True, f"Diário encontrado! PDF em Base64: {len(arquivo['arquivo'])} caracteres")
                            print(f"    Total de páginas: {arquivo.get('totalPaginas', 'N/A')}")
                            success_count += 1
                            return True, test_date
                        else:
                            print(f"    ⚠️  Resposta sem arquivo PDF")
                    else:
                        print(f"    ⚠️  Resposta sem dados")
                else:
                    print(f"    ⚠️  Resposta inválida ou vazia")
            elif response.status_code == 404:
                print(f"    ⚠️  Diário não encontrado para esta data (404)")
            elif response.status_code == 401:
                print_result(False, f"ERRO 401: Requer autenticação! Status: {response.status_code}")
                return False, None
            else:
                print_result(False, f"Status inesperado: {response.status_code}")
                print(f"    Response: {response.text[:200]}")
        except requests.exceptions.Timeout:
            print_result(False, f"Timeout ao acessar API")
        except requests.exceptions.RequestException as e:
            print_result(False, f"Erro na requisição: {e}")
        except Exception as e:
            print_result(False, f"Erro inesperado: {e}")
    
    if success_count == 0:
        print_result(False, "Nenhum diário encontrado nas últimas 7 dias")
        return False, None
    
    return True, test_dates[0]

def test_download_direct():
    """Teste 2: Download direto do PDF."""
    print_test("Download Direto do PDF")
    
    # Testar com uma data recente (últimos 7 dias)
    test_dates = []
    for i in range(7):
        test_date = date.today() - timedelta(days=i)
        test_dates.append(test_date)
    
    for test_date in test_dates:
        try:
            url = (
                f"https://www.jornalminasgerais.mg.gov.br/modulos/"
                f"www.jornalminasgerais.mg.gov.br//diarioOficial/"
                f"{test_date.strftime('%Y/%m/%d')}/jornal/"
                f"caderno1_{test_date.strftime('%Y-%m-%d')}.pdf"
            )
            
            print(f"\n  Testando data: {test_date.strftime('%Y-%m-%d')}")
            print(f"  URL: {url[:80]}...")
            
            response = requests.get(url, timeout=30, stream=True)
            
            if response.status_code == 200:
                # Verificar se é realmente um PDF
                content_type = response.headers.get('Content-Type', '')
                content_length = response.headers.get('Content-Length', '0')
                
                if 'pdf' in content_type.lower() or response.content[:4] == b'%PDF':
                    size_mb = int(content_length) / (1024 * 1024) if content_length else len(response.content) / (1024 * 1024)
                    print_result(True, f"PDF baixado com sucesso! Tamanho: {size_mb:.2f} MB")
                    print(f"    Content-Type: {content_type}")
                    return True, test_date
                else:
                    print_result(False, f"Resposta não é PDF. Content-Type: {content_type}")
            elif response.status_code == 404:
                print(f"    ⚠️  PDF não encontrado para esta data (404)")
            elif response.status_code == 401:
                print_result(False, f"ERRO 401: Requer autenticação! Status: {response.status_code}")
                return False, None
            else:
                print_result(False, f"Status inesperado: {response.status_code}")
        except requests.exceptions.Timeout:
            print_result(False, f"Timeout ao baixar PDF")
        except requests.exceptions.RequestException as e:
            print_result(False, f"Erro na requisição: {e}")
        except Exception as e:
            print_result(False, f"Erro inesperado: {e}")
    
    print_result(False, "Nenhum PDF encontrado nas últimas 7 dias")
    return False, None

def explain_api_beta():
    """Explica o que é a API Beta."""
    print_test("O que é a API Beta?")
    print("""
A API Beta é uma versão alternativa da API do Diário Oficial que:

1. Endpoint diferente:
   - API Beta: https://www.jornalminasgerais.mg.gov.br/api/beta/jornal
   - API v1: https://www.jornalminasgerais.mg.gov.br/api/v1/Jornal/...

2. Requer autenticação:
   - Usa HTTP Basic Authentication
   - Precisa de IOF_USERNAME e IOF_PASSWORD
   - Sem credenciais, retorna erro 401

3. Funcionalidades:
   - get_latest(): Busca o diário mais recente
   - get_by_date(): Busca diário por data específica
   - Retorna dados já processados (não precisa extrair PDF)

4. Por que "Beta"?
   - Pode ser uma versão experimental
   - Pode estar em desenvolvimento
   - Pode ter recursos diferentes da v1

5. Diferença prática:
   - API Beta: Retorna dados JSON já processados
   - API v1: Retorna PDF em Base64 (precisa extrair)
   - Download direto: Retorna PDF binário direto

No código atual, a API Beta está implementada mas NÃO é usada.
O sistema usa a API v1 que não precisa de credenciais.
""")

def main():
    """Executa todos os testes."""
    print("="*60)
    print("TESTE DE ACESSO AO DIÁRIO OFICIAL (SEM CREDENCIAIS)")
    print("="*60)
    
    # Explicar API Beta
    explain_api_beta()
    
    results = []
    
    # Teste 1: API v1
    success, test_date = test_api_v1()
    results.append(success)
    
    # Teste 2: Download direto
    success, _ = test_download_direct()
    results.append(success)
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"✅ Testes passaram: {passed}/{total}")
    print(f"❌ Testes falharam: {total - passed}/{total}")
    
    if all(results):
        print("\n🎉 AMBOS OS MÉTODOS FUNCIONAM SEM CREDENCIAIS!")
        print("\n📝 Conclusão:")
        print("   Você NÃO precisa de credenciais IOF para usar o sistema.")
        print("   O sistema pode funcionar completamente sem autenticação.")
    elif results[0]:
        print("\n⚠️  API v1 funciona, mas download direto falhou.")
        print("   Você pode usar a API v1 sem credenciais.")
    elif results[1]:
        print("\n⚠️  Download direto funciona, mas API v1 falhou.")
        print("   Você pode usar download direto sem credenciais.")
    else:
        print("\n❌ Ambos os métodos falharam.")
        print("   Pode ser que:")
        print("   - Não há diários nas datas testadas")
        print("   - A API mudou e agora requer autenticação")
        print("   - Problema de conexão")
    
    sys.exit(0 if all(results) else 1)

if __name__ == '__main__':
    main()
