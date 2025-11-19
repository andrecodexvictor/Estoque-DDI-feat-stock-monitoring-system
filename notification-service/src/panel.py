# -*- coding: utf-8 -*-
import requests
import time
import os

def clear_screen():
    """Limpa o terminal para Windows ou Linux/macOS."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_panel():
    """Busca e exibe os eventos do serviço de notificação de dados."""
    while True:
        try:
            # A URL do serviço Flask, acessível dentro da mesma rede Docker
            response = requests.get('http://notification-service:3003/api/eventos')
            response.raise_for_status()  # Lança uma exceção para respostas com erro
            eventos = response.json()

            clear_screen()
            print("--- Painel de Eventos Recentes (Notification Service) ---")
            print("-" * 60)

            if not eventos:
                print("Nenhum evento recente para exibir.")
            else:
                for evento in eventos:
                    print(
                        f"Produto: {evento['nome_produto']} ({evento['produto_id']}) | "
                        f"Operação: {evento['tipo_operacao']} | "
                        f"Quantidade: {evento['quantidade']} | "
                        f"Timestamp: {evento['timestamp']}"
                    )

            print("-" * 60)
            print("Atualizando em 5 segundos...")

        except requests.exceptions.RequestException as e:
            clear_screen()
            print(f"Não foi possível conectar ao serviço de notificação de dados: {e}")
            print("Tentando novamente em 5 segundos...")

        time.sleep(5)

if __name__ == '__main__':
    display_panel()
