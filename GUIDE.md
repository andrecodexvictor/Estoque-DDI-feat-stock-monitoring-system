# Guia do Sistema de Monitoramento de Estoque

Este guia explica como visualizar as mensagens geradas, modificar o painel de eventos e entender o funcionamento do sistema.

## 1. Como ver as mensagens geradas

O sistema possui duas formas principais de visualizar as mensagens (eventos de estoque):

### A. Painéis Web
Após iniciar o sistema, você pode acessar os seguintes painéis no seu navegador:

*   **Painel de Ingestão de Dados:** `http://localhost:3001/panel`
    *   Mostra os eventos brutos gerados pelo simulador de vendas/reposição.
    *   Fonte de dados: `data-ingestion-service`.
*   **Painel de Monitoramento:** `http://localhost:3002/panel`
    *   Mostra os eventos processados e **alertas de estoque crítico**.
    *   Fonte de dados: `monitoring-service`.

### B. Painel via Terminal (Console)
Existe um script Python que exibe os eventos diretamente no terminal:

1.  Certifique-se de que o sistema está rodando.
2.  Abra um novo terminal.
3.  Execute o script:
    ```bash
    python monitoring-service/src/panel.py
    ```
    *Nota: Este script tenta conectar em `http://monitoring-service:3002`, o que funciona dentro da rede Docker. Se rodar fora (no seu Windows), você precisará editar o arquivo `monitoring-service/src/panel.py` e trocar `monitoring-service` por `localhost`.*

### C. Logs do Docker
Você pode ver tudo o que está acontecendo nos logs dos contêineres:
```bash
docker-compose logs -f
```

## 2. Como fazer alterações no Painel

### Para alterar o Painel Web (HTML/Visual)
Os arquivos de template estão localizados em:
*   `monitoring-service/src/templates/panel.html` (Painel Principal)
*   `data-ingestion-service/src/templates/panel.html` (Painel de Ingestão)

**Exemplo de alteração:**
Se quiser mudar a cor de fundo ou adicionar uma nova coluna na tabela de eventos, edite o arquivo `panel.html` correspondente. O código usa HTML e JavaScript simples para buscar os dados da API `/api/eventos` a cada 2 segundos.

### Para alterar o Painel do Terminal
Edite o arquivo:
*   `monitoring-service/src/panel.py`

Você pode alterar a função `display_panel()` para mudar a formatação do texto ou filtrar quais eventos são exibidos.

## 3. Funcionamento do App (Fluxo de Dados)

1.  **Geração (Data Ingestion):**
    *   O serviço `data-ingestion-service` gera aleatoriamente vendas e reposições.
    *   Ele envia esses eventos para o **Kafka** (tópico `stock-updates`).
2.  **Processamento (Monitoring):**
    *   O serviço `monitoring-service` consome as mensagens do Kafka.
    *   Ele atualiza o estoque interno em memória.
    *   Se o estoque cair abaixo de 10 unidades, ele gera um **Alerta** e envia para o tópico `stock-alerts`.
3.  **Visualização:**
    *   As APIs `/api/eventos` em ambos os serviços retornam os últimos 50 eventos da memória para serem exibidos nos painéis.

## 4. Como Rodar o Sistema

Certifique-se de ter o Docker e Docker Compose instalados.

1.  Na pasta raiz do projeto, execute:
    ```bash
    docker-compose up --build
    ```
2.  Aguarde até que todos os serviços (kafka, zookeeper, services) estejam "Up".
3.  Acesse os links mencionados na seção 1.
