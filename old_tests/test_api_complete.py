#!/usr/bin/env python3
"""Script de teste completo para API - Testa todos os endpoints."""
import sys
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:5000/api"

def print_test(name: str):
    """Imprime cabeçalho de teste."""
    print(f"\n{'='*60}")
    print(f"TESTE: {name}")
    print('='*60)

def print_result(success: bool, message: str = ""):
    """Imprime resultado do teste."""
    status = "✅ PASSOU" if success else "❌ FALHOU"
    print(f"{status}: {message}")

def test_features():
    """Teste 1: Verificar features disponíveis."""
    print_test("Features API")
    try:
        response = requests.get(f"{BASE_URL}/features")
        if response.status_code == 200:
            data = response.json()
            print_result(True, f"Features: {data}")
            return True, data
        else:
            print_result(False, f"Status code: {response.status_code}")
            return False, None
    except Exception as e:
        print_result(False, f"Erro: {e}")
        return False, None

def test_list_configs():
    """Teste 2: Listar configurações."""
    print_test("Listar Configurações")
    try:
        response = requests.get(f"{BASE_URL}/search/configs")
        if response.status_code == 200:
            data = response.json()
            print_result(True, f"Encontradas {len(data)} configurações")
            return True, data
        else:
            print_result(False, f"Status code: {response.status_code}")
            return False, None
    except Exception as e:
        print_result(False, f"Erro: {e}")
        return False, None

def test_create_config():
    """Teste 3: Criar configuração."""
    print_test("Criar Configuração")
    try:
        payload = {
            "label": "Teste Automatizado",
            "description": "Configuração criada por teste automatizado",
            "attach_csv": False,
            "mail_to": ["teste@example.com"],
            "mail_subject": "Teste Automatizado",
            "terms": [
                {"term": "licitação", "exact": False},
                {"term": "pregão", "exact": True}
            ]
        }
        response = requests.post(
            f"{BASE_URL}/search/configs",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 201:
            data = response.json()
            config_id = data.get('id')
            print_result(True, f"Configuração criada com ID: {config_id}")
            return True, config_id
        else:
            print_result(False, f"Status code: {response.status_code}, Response: {response.text}")
            return False, None
    except Exception as e:
        print_result(False, f"Erro: {e}")
        return False, None

def test_get_config(config_id: int):
    """Teste 4: Buscar configuração por ID."""
    print_test(f"Buscar Configuração ID {config_id}")
    try:
        response = requests.get(f"{BASE_URL}/search/configs/{config_id}")
        if response.status_code == 200:
            data = response.json()
            print_result(True, f"Configuração encontrada: {data.get('label')}")
            return True, data
        else:
            print_result(False, f"Status code: {response.status_code}")
            return False, None
    except Exception as e:
        print_result(False, f"Erro: {e}")
        return False, None

def test_update_config(config_id: int):
    """Teste 5: Atualizar configuração."""
    print_test(f"Atualizar Configuração ID {config_id}")
    try:
        payload = {
            "label": "Teste Automatizado Atualizado",
            "description": "Descrição atualizada pelo teste",
            "attach_csv": True,
            "mail_to": ["novo@example.com", "outro@example.com"],
            "mail_subject": "Assunto Atualizado",
            "terms": [
                {"term": "licitação", "exact": False},
                {"term": "concorrência", "exact": True}
            ]
        }
        response = requests.put(
            f"{BASE_URL}/search/configs/{config_id}",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print_result(True, f"Configuração atualizada: {data.get('label')}")
            # Verificar se foi realmente atualizada
            if data.get('label') == payload['label']:
                print_result(True, "Verificação: Label atualizado corretamente")
            else:
                print_result(False, "Verificação: Label não foi atualizado")
            return True, data
        else:
            print_result(False, f"Status code: {response.status_code}, Response: {response.text}")
            return False, None
    except Exception as e:
        print_result(False, f"Erro: {e}")
        return False, None

def test_delete_config(config_id: int):
    """Teste 6: Deletar configuração."""
    print_test(f"Deletar Configuração ID {config_id}")
    try:
        response = requests.delete(f"{BASE_URL}/search/configs/{config_id}")
        if response.status_code == 204:
            print_result(True, "Configuração deletada com sucesso")
            # Verificar se foi realmente deletada
            check_response = requests.get(f"{BASE_URL}/search/configs/{config_id}")
            if check_response.status_code == 404:
                print_result(True, "Verificação: Configuração não existe mais")
            else:
                print_result(False, "Verificação: Configuração ainda existe")
            return True
        else:
            print_result(False, f"Status code: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Erro: {e}")
        return False

def test_list_active_only():
    """Teste 7: Listar com filtro active_only."""
    print_test("Listar com filtro active_only")
    try:
        # Listar apenas ativas
        response = requests.get(f"{BASE_URL}/search/configs?active_only=true")
        if response.status_code == 200:
            active_configs = response.json()
            print_result(True, f"Configurações ativas: {len(active_configs)}")
        
        # Listar todas
        response = requests.get(f"{BASE_URL}/search/configs?active_only=false")
        if response.status_code == 200:
            all_configs = response.json()
            print_result(True, f"Total de configurações: {len(all_configs)}")
            return True
        else:
            print_result(False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Erro: {e}")
        return False

def test_validation_errors():
    """Teste 8: Validações de entrada."""
    print_test("Validações de Entrada")
    results = []
    
    # Teste 8a: Criar sem label
    try:
        payload = {
            "description": "Sem label",
            "terms": [{"term": "teste", "exact": False}]
        }
        response = requests.post(
            f"{BASE_URL}/search/configs",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 422:
            print_result(True, "Validação: Criar sem label retorna erro 422")
            results.append(True)
        else:
            print_result(False, f"Validação: Esperava 422, recebeu {response.status_code}")
            results.append(False)
    except Exception as e:
        print_result(False, f"Erro: {e}")
        results.append(False)
    
    # Teste 8b: Criar com mais de 5 termos
    try:
        payload = {
            "label": "Teste",
            "terms": [
                {"term": "termo1", "exact": False},
                {"term": "termo2", "exact": False},
                {"term": "termo3", "exact": False},
                {"term": "termo4", "exact": False},
                {"term": "termo5", "exact": False},
                {"term": "termo6", "exact": False}
            ]
        }
        response = requests.post(
            f"{BASE_URL}/search/configs",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 422:
            print_result(True, "Validação: Mais de 5 termos retorna erro 422")
            results.append(True)
        else:
            print_result(False, f"Validação: Esperava 422, recebeu {response.status_code}")
            results.append(False)
    except Exception as e:
        print_result(False, f"Erro: {e}")
        results.append(False)
    
    # Teste 8c: Buscar configuração inexistente
    try:
        response = requests.get(f"{BASE_URL}/search/configs/99999")
        if response.status_code == 404:
            print_result(True, "Validação: Configuração inexistente retorna 404")
            results.append(True)
        else:
            print_result(False, f"Validação: Esperava 404, recebeu {response.status_code}")
            results.append(False)
    except Exception as e:
        print_result(False, f"Erro: {e}")
        results.append(False)
    
    return all(results)

def main():
    """Executa todos os testes."""
    print("="*60)
    print("TESTE COMPLETO DA API - Notificador IOF MG")
    print("="*60)
    print("\n⚠️  Certifique-se de que o servidor Flask está rodando!")
    print("   Execute: uv run python run.py\n")
    
    # Verificar se servidor está rodando
    try:
        response = requests.get(f"{BASE_URL}/features", timeout=2)
    except requests.exceptions.ConnectionError:
        print("❌ ERRO: Servidor Flask não está rodando!")
        print("   Execute: uv run python run.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERRO: {e}")
        sys.exit(1)
    
    results = []
    created_config_id = None
    
    # Executar testes
    success, _ = test_features()
    results.append(success)
    
    success, _ = test_list_configs()
    results.append(success)
    
    success, config_id = test_create_config()
    results.append(success)
    if config_id:
        created_config_id = config_id
    
    if created_config_id:
        success, _ = test_get_config(created_config_id)
        results.append(success)
        
        success, _ = test_update_config(created_config_id)
        results.append(success)
        
        success = test_delete_config(created_config_id)
        results.append(success)
    
    success = test_list_active_only()
    results.append(success)
    
    success = test_validation_errors()
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
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        sys.exit(0)
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM")
        sys.exit(1)

if __name__ == '__main__':
    main()
