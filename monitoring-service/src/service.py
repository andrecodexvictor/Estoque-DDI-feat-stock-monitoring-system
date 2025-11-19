# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify
from threading import Thread, Lock
import json
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable
import time
from datetime import datetime
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Estado do Serviço ---
# Dicionário para manter o estoque atual de cada produto.
# A chave é o 'produto_id', o valor é a quantidade em estoque.
estoque_produtos = {}
# Lista para armazenar os eventos processados (consumidos e produzidos) para o painel.
eventos_recentes = []
# Lock para garantir acesso seguro às estruturas de dados compartilhadas entre threads.
lock = Lock()
# Limite crítico de estoque
LIMITE_CRITICO = 10

# --- Conexão com Kafka ---

def conectar_kafka_com_retry(kafka_class, topic=None, max_tentativas=15, delay=5):
    """
    Função genérica para conectar ao Kafka com múltiplas tentativas.
    Funciona tanto para KafkaConsumer quanto para KafkaProducer.
    """
    for tentativa in range(max_tentativas):
        try:
            if kafka_class == KafkaConsumer:
                # Conexão para o Consumer
                client = KafkaConsumer(
                    topic,
                    bootstrap_servers='kafka:9092',
                    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                    auto_offset_reset='earliest', # Garante que o consumidor leia desde o início do tópico
                    group_id='monitoring-group' # ID do grupo de consumidores
                )
            else:
                # Conexão para o Producer
                client = KafkaProducer(
                    bootstrap_servers='kafka:9092',
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    api_version=(0, 10, 1)
                )

            logger.info(f"Conexão com o Kafka ({kafka_class.__name__}) estabelecida com sucesso!")
            return client
        except NoBrokersAvailable:
            logger.warning(f"Tentativa {tentativa + 1}/{max_tentativas} de conectar ao Kafka falhou. Tentando novamente em {delay}s...")
            time.sleep(delay)
    logger.error(f"Não foi possível conectar ao Kafka ({kafka_class.__name__}) após múltiplas tentativas.")
    raise Exception(f"Não foi possível conectar ao Kafka como {kafka_class.__name__}")

# --- Lógica do Serviço ---

def kafka_consumer_loop():
    """
    Thread que consome eventos do tópico 'stock-updates', processa a lógica de negócio
    e publica alertas no tópico 'stock-alerts' se necessário.
    """
    consumer = conectar_kafka_com_retry(KafkaConsumer, 'stock-updates')
    producer = conectar_kafka_com_retry(KafkaProducer)

    for mensagem in consumer:
        evento = mensagem.value
        logger.info(f"[MONITORING] Evento de estoque recebido: {evento}")

        produto_id = evento['produto_id']
        tipo_operacao = evento['tipo_operacao']
        quantidade = evento['quantidade']

        with lock:
            # Pega o estoque atual ou define um valor inicial (ex: 50) se o produto for novo
            estoque_atual = estoque_produtos.get(produto_id, 50)

            # Atualiza o estoque com base na operação
            if tipo_operacao == 'venda':
                novo_estoque = estoque_atual - quantidade
            elif tipo_operacao == 'reposicao':
                novo_estoque = estoque_atual + quantidade
            else:
                novo_estoque = estoque_atual # Operação desconhecida, não altera o estoque

            estoque_produtos[produto_id] = novo_estoque
            logger.info(f"Estoque do produto '{produto_id}' atualizado para: {novo_estoque}")

            # Adiciona o evento de 'stock-updates' ao painel
            evento['servico_origem'] = 'data-ingestion-service'
            eventos_recentes.insert(0, evento)

            # --- Regra de Negócio: Verificar se o estoque está abaixo do limite crítico ---
            if novo_estoque < LIMITE_CRITICO:
                alerta = {
                    "produto_id": produto_id,
                    "nome_produto": evento["nome_produto"],
                    "estoque_atual": novo_estoque,
                    "limite_critico": LIMITE_CRITICO,
                    "severidade": "ALTA",
                    "mensagem": f"Estoque crítico para {evento['nome_produto']}! Apenas {novo_estoque} unidades restantes.",
                    "timestamp": datetime.now().isoformat()
                }

                # Publica o alerta no tópico 'stock-alerts'
                producer.send('stock-alerts', alerta)
                producer.flush()
                logger.warning(f"[MONITORING] Alerta de estoque crítico gerado e publicado: {alerta}")

                # Adiciona o alerta gerado ao painel
                alerta['servico_origem'] = 'monitoring-service'
                eventos_recentes.insert(0, alerta)

            # Mantém a lista de eventos com no máximo 50 itens
            if len(eventos_recentes) > 50:
                eventos_recentes.pop()

# --- Rotas Flask ---

@app.route('/panel')
def panel():
    """Rota que renderiza o painel de visualização de eventos."""
    return render_template('panel.html', servico="Monitoring Service")

@app.route('/api/eventos')
def get_eventos():
    """API que fornece os eventos recentes em formato JSON para o frontend."""
    with lock:
        return jsonify(eventos_recentes)

# --- Inicialização ---

if __name__ == '__main__':
    # Inicia a thread do consumidor/processador Kafka em background
    kafka_thread = Thread(target=kafka_consumer_loop, daemon=True)
    kafka_thread.start()

    # Inicia o servidor Flask
    app.run(host='0.0.0.0', port=3002, debug=False)
