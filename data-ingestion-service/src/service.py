# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify
from threading import Thread
import time
import json
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import random
from datetime import datetime
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Lista global para armazenar os últimos 50 eventos gerados por este serviço
eventos_recentes = []

def conectar_kafka_com_retry(delay=5):
    """Tenta conectar ao Kafka indefinidamente até conseguir."""
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                api_version=(0, 10, 1) # Versão compatível com o broker Kafka
            )
            logger.info("Conexão com o Kafka estabelecida com sucesso!")
            return producer
        except NoBrokersAvailable:
            logger.warning(f"Falha ao conectar ao Kafka. Tentando novamente em {delay}s...")
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Erro inesperado ao conectar ao Kafka: {e}. Tentando novamente em {delay}s...")
            time.sleep(delay)

def kafka_producer_loop():
    """
    Thread que simula a entrada de dados (vendas e reposições)
    e publica eventos no tópico 'stock-updates' do Kafka.
    """
    while True:
        try:
            producer = conectar_kafka_com_retry()

            produtos = [
                {"id": "PROD001", "nome": "Mouse Gamer RGB"},
                {"id": "PROD002", "nome": "Teclado Mecânico"},
                {"id": "PROD003", "nome": "Headset Gamer 7.1"},
                {"id": "PROD004", "nome": "Monitor Ultrawide 29\""},
                {"id": "PROD005", "nome": "Cadeira Gamer"},
            ]

            while True:
                try:
                    produto = random.choice(produtos)
                    # Aumentar a probabilidade de vendas em relação a reposições
                    tipo_operacao = random.choice(["venda", "venda", "venda", "reposicao"])

                    if tipo_operacao == "venda":
                        quantidade = random.randint(1, 5) # Vendas em pequenas quantidades
                    else:
                        quantidade = random.randint(10, 30) # Reposições em grandes quantidades

                    # O evento representa a *alteração* no estoque
                    evento = {
                        "produto_id": produto["id"],
                        "nome_produto": produto["nome"],
                        "quantidade": quantidade, # Quantidade é sempre positiva, o tipo define a operação
                        "tipo_operacao": tipo_operacao,
                        "timestamp": datetime.now().isoformat()
                    }

                    # Envia o evento para o tópico 'stock-updates'
                    producer.send('stock-updates', evento)
                    producer.flush() # Garante que a mensagem foi enviada

                    # Adiciona o evento à lista de eventos recentes para exibição no painel
                    eventos_recentes.insert(0, evento)
                    if len(eventos_recentes) > 50:
                        eventos_recentes.pop()

                    logger.info(f"[DATA INGESTION] Evento publicado: {evento}")

                    # Aguarda um tempo aleatório antes de gerar o próximo evento
                    time.sleep(random.randint(3, 8))

                except Exception as e:
                    logger.error(f"Erro ao publicar evento no Kafka: {e}")
                    # Sai do loop interno para tentar reconectar
                    break
        
        except Exception as e:
            logger.error(f"Erro fatal na thread do produtor: {e}. Reiniciando em 5s...")
            time.sleep(5)

@app.route('/panel')
def panel():
    """Rota que renderiza o painel de visualização de eventos."""
    return render_template('panel.html', servico="Data Ingestion Service")

@app.route('/api/eventos')
def get_eventos():
    """API que fornece os eventos recentes em formato JSON para o frontend."""
    return jsonify(eventos_recentes)

if __name__ == '__main__':
    # Inicia a thread do produtor Kafka em background
    # O 'daemon=True' garante que a thread será encerrada quando o processo principal terminar
    kafka_thread = Thread(target=kafka_producer_loop, daemon=True)
    kafka_thread.start()

    # Inicia o servidor Flask
    app.run(host='0.0.0.0', port=3001, debug=False)
