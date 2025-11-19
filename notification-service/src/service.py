# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify
from threading import Thread, Lock
import json
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import time
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Estado do Serviço ---
# Lista para armazenar os alertas recebidos para exibição no painel.
alertas_recentes = []
# Lock para garantir acesso seguro à lista de alertas entre threads.
lock = Lock()

# --- Conexão com Kafka ---

def conectar_kafka_consumer_com_retry(topic, max_tentativas=15, delay=5):
    """Tenta conectar um KafkaConsumer com múltiplas tentativas."""
    for tentativa in range(max_tentativas):
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers='kafka:9092',
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                auto_offset_reset='earliest', # Garante que leia desde o início
                group_id='notification-group' # Grupo de consumidores para este serviço
            )
            logger.info(f"Conexão com o Kafka (Consumer) no tópico '{topic}' estabelecida com sucesso!")
            return consumer
        except NoBrokersAvailable:
            logger.warning(f"Tentativa {tentativa + 1}/{max_tentativas} de conectar ao Kafka falhou. Tentando novamente em {delay}s...")
            time.sleep(delay)
    logger.error(f"Não foi possível conectar ao Kafka no tópico '{topic}' após múltiplas tentativas.")
    raise Exception(f"Não foi possível conectar ao Kafka no tópico '{topic}'")

# --- Lógica do Serviço ---

def kafka_consumer_loop():
    """
    Thread que consome eventos de alerta do tópico 'stock-alerts'
    e os armazena para exibição no painel.
    """
    consumer = conectar_kafka_consumer_com_retry('stock-alerts')

    for mensagem in consumer:
        alerta = mensagem.value
        logger.info(f"[NOTIFICATION] Alerta de estoque recebido: {alerta}")

        with lock:
            # Adiciona o alerta à lista de alertas recentes
            alerta['servico_origem'] = 'monitoring-service'
            alertas_recentes.insert(0, alerta)

            # Mantém a lista com no máximo 50 alertas
            if len(alertas_recentes) > 50:
                alertas_recentes.pop()

            # Simulação de notificação: aqui poderia ser implementado o envio
            # de um e-mail, SMS, ou uma chamada para outra API.
            # Para este trabalho, apenas um log detalhado é suficiente.
            logger.info("--- SIMULAÇÃO DE NOTIFICAÇÃO ---")
            logger.info(f"  Tipo: Alerta de Estoque Crítico")
            logger.info(f"  Produto: {alerta['nome_produto']} (ID: {alerta['produto_id']})")
            logger.info(f"  Estoque Atual: {alerta['estoque_atual']} (Limite: {alerta['limite_critico']})")
            logger.info(f"  Mensagem: {alerta['mensagem']}")
            logger.info("---------------------------------")

# --- Rotas Flask ---

@app.route('/panel')
def panel():
    """Rota que renderiza o painel de visualização de alertas."""
    return render_template('panel.html', servico="Notification Service")

@app.route('/api/eventos')
def get_eventos():
    """
    API que fornece os alertas recentes em formato JSON para o frontend.
    Renomeado para '/api/eventos' para manter a consistência com os outros painéis.
    """
    with lock:
        return jsonify(alertas_recentes)

# --- Inicialização ---

if __name__ == '__main__':
    # Inicia a thread do consumidor Kafka em background
    kafka_thread = Thread(target=kafka_consumer_loop, daemon=True)
    kafka_thread.start()

    # Inicia o servidor Flask
    app.run(host='0.0.0.0', port=3003, debug=False)
