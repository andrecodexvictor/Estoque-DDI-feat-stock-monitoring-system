# Guia de Apresentação: Sistema de Monitoramento de Estoque Distribuído

Este documento serve como um roteiro completo para apresentar o funcionamento, a arquitetura e o código deste projeto.

## 1. Visão Geral do Projeto

**Objetivo:** Simular um sistema de varejo em tempo real onde vendas e reposições ocorrem e precisam ser monitoradas instantaneamente para evitar falta de estoque.

**Arquitetura (Microserviços + Event-Driven):**
O sistema utiliza uma arquitetura baseada em eventos com **Apache Kafka**.

1.  **Data Ingestion Service (Produtor):** Simula o PDV (Ponto de Venda) e o Estoque físico. Gera eventos de `venda` e `reposicao` aleatoriamente.
2.  **Kafka (Message Broker):** O "carteiro" que transporta as mensagens entre os serviços de forma assíncrona e desacoplada.
3.  **Monitoring Service (Consumidor):** O "cérebro". Lê os eventos do Kafka, atualiza o saldo de estoque em memória e verifica regras de negócio (Ex: Estoque Baixo).
4.  **Notification Service:** (Opcional/Expansão) Escuta alertas críticos.

### Ponto Crítico: Coreografia vs. Orquestração

É fundamental explicar isso corretamente na sua apresentação:

*   **Infraestrutura (Docker):** Sim, usamos **Orquestração de Containers**. O `docker-compose` é o maestro que sobe, conecta e gerencia a vida dos serviços.
*   **Lógica de Negócio (Kafka):** O padrão utilizado é **Coreografia (Choreography)**, não Orquestração Centralizada.
    *   *Por que?* Na orquestração, um "chefe" manda os outros trabalharem. Na coreografia (nosso caso), os serviços reagem a eventos. O "Data Ingestion" não manda o "Monitoring" atualizar; ele apenas avisa "Vendi um item", e o "Monitoring" reage.
    *   *Vantagem:* Isso deixa o sistema muito mais rápido e desacoplado. Se o Monitoramento cair, o Ingestion continua vendendo.

---

## 2. Explicação do Código (O que mostrar)

Ao apresentar o código, foque nestes arquivos principais:

### A. `docker-compose.yml`
*   **O que falar:** "Aqui definimos nossa infraestrutura. Temos o Zookeeper e Kafka para mensageria, e nossos serviços Python rodando em containers isolados, mas conectados pela rede interna."

### B. `data-ingestion-service/src/service.py`
*   **Destaque:** Função `kafka_producer_loop`.
*   **O que falar:** "Este loop infinito simula a vida real. Ele escolhe um produto aleatório e gera uma venda ou reposição. Em seguida, envia esse evento para o tópico `stock-updates` do Kafka."

### C. `monitoring-service/src/service.py`
*   **Destaque:** Função `kafka_consumer_loop` e a lógica `if novo_estoque < LIMITE_CRITICO`.
*   **O que falar:** "Aqui é onde a mágica acontece. O serviço lê a mensagem do Kafka, atualiza o estoque e, se estiver abaixo de 10 unidades, gera automaticamente um ALERTA de severidade ALTA."

---

## 3. Como Rodar o Projeto

Para iniciar a demonstração, execute no terminal (na pasta raiz):

```bash
docker-compose up --build
```

*Aguarde até ver logs indicando que o Kafka e os serviços iniciaram.*

---

## 4. Roteiro de Demonstração (Demo Script)

Siga estes passos para uma apresentação fluida:

### Passo 1: O Fluxo de Dados (Ingestão)
*   **Ação:** Abra o navegador em `http://localhost:3001/panel`.
*   **Narrativa:** "Aqui vemos o **Data Ingestion Service**. Ele está gerando vendas (vermelho) e reposições (verde) em tempo real. Cada linha aqui é uma mensagem sendo enviada para o Kafka."

### Passo 2: O Processamento (Monitoramento)
*   **Ação:** Abra uma nova aba em `http://localhost:3002/panel`.
*   **Narrativa:** "Este é o **Monitoring Service**. Ele não gera dados, ele apenas *escuta*. Observe que ele recebe os mesmos eventos quase instantaneamente."

### Passo 3: O Alerta de Estoque Crítico
*   **Ação:** Fique observando o painel de Monitoramento (3002).
*   **Narrativa:** "O sistema tem uma regra de negócio: se o estoque de um produto cair abaixo de 10, um alerta é gerado."
*   **O que esperar:** Aguarde aparecer uma linha **LARANJA/AMARELA**.
*   **Narrativa:** "Vejam! Um alerta de 'Estoque Crítico' foi gerado. Isso não veio do simulador, foi calculado pelo serviço de monitoramento baseados nos eventos recebidos."

### Passo 4: O Serviço de Notificação
*   **Ação:** Abra uma nova aba em `http://localhost:3003/panel`.
*   **Narrativa:** "E aqui temos o **Notification Service**. Ele escuta especificamente o tópico de alertas. Assim que o Monitoramento gerou o alerta crítico, este serviço o recebeu para disparar e-mails, SMS ou push notifications (simulado aqui)."


### Passo 5: Visão "Hacker" (Console)
*   **Ação:** Abra um terminal e rode: `python monitoring-service/src/panel.py`
*   **Narrativa:** "Para administradores de sistemas, também temos uma visão de console que consome a mesma API, mostrando a flexibilidade de ter múltiplos frontends consumindo os mesmos dados."

---

## 5. Perguntas Comuns (FAQ)

*   **Por que usar Kafka?** Para garantir que, mesmo se o monitoramento cair, as vendas não sejam perdidas (elas ficam na fila do Kafka).
*   **Onde estão os dados?** Neste protótipo, estão em memória (variáveis Python), mas em produção usariamos um banco de dados (SQL/NoSQL).

---

## 6. Comandos Úteis do Docker (Para Impressionar)

Durante a apresentação, você pode usar estes comandos para mostrar que domina a ferramenta e verificar o status real da infraestrutura:

*   **Listar Containers Rodando (`docker ps`):**
    ```bash
    docker container ls
    ```
    *Mostra todos os containers ativos, IDs, imagens e portas mapeadas.*

*   **Ver Consumo de Recursos (CPU/Memória):**
    ```bash
    docker stats
    ```
    *Exibe uma tabela em tempo real com o uso de CPU e Memória de cada serviço. Ótimo para mostrar o "peso" de cada container.*

*   **Listar Redes:**
    ```bash
    docker network ls
    ```
    *Mostra a rede interna (bridge) criada para conectar os microsserviços.*

