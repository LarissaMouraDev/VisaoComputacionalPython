# 🚀 Sistema IoT - Instruções de Execução

## Larissa de Freitas Moura -555136
## Guilherme Francisco - 557648

**MotoScan** é uma solução integrada que combina IoT, visão computacional e modelos de IA generativa para automatizar o monitoramento, análise e geração de insights para frotas de motocicletas.  

Este sistema foi concebido para empresas que operam com grandes frotas, como locadoras, delivery ou logística, e que desejam reduzir custos de manutenção, aumentar a eficiência e ter controle automatizado.

---

## 📋 Funcionalidades

### 1. Visão Computacional  
- Identificação automática de modelos de motocicletas (ex: E, Sport 110i, Pop)  
- Análise visual do estado de conservação (classificação por setores: A, B, C)  
- Geração de “placas internas” para controle / rastreamento interno  

### 2. IA Generativa  
- Geração de relatórios técnicos e contextualizados por modelo  
- Cronogramas de manutenção personalizados  
- Consulta em linguagem natural (ex: “Quais motos precisam de revisão hoje?”)  
- Recomendações técnicas específicas para cada modelo  

### 3. Monitoramento IoT  
- Simulação e integração de sensores: GPS, temperatura, combustível, acelerômetro  
- Dashboard em tempo real com métricas da frota  
- Alertas automáticos para condições críticas (ex: temperatura alta, bateria baixa)  
- Comunicação via **MQTT** para integração com dispositivos  

---

## 🏗️ Arquitetura / Componentes principais

| Módulo / Arquivo | Responsabilidade |
|------------------|--------------------|
| `motoscan_vision.py` | Lógica de detecção, classificação e análise de imagens / vídeo |
| `motoscan_ai.py` | Geração de relatórios, recomendações, consultas em linguagem natural |
| `iot_sensors.py` | Simulação / leitura de sensores IoT (GPS, temperatura, aceleração etc.) |
| `mqtt_client.py` | Cliente MQTT para envio / recepção de dados entre dispositivos e servidor |
| `dashboard_iot.py` | Interface web / dashboard para visualização dos dados em tempo real |
| `app.py` | Ponto de entrada, configura rotas, integra módulos, inicia o servidor |
| `requirements.txt` | Bibliotecas / dependências necessárias |

---

## 🛠️ Pré-requisitos & Instalação

1. Ter **Python 3.8+** instalado  
2. Clonar este repositório  
   ```bash
   git clone https://github.com/LarissaMouraDev/VisaoComputacionalPython.git
   cd VisaoComputacionalPython
Criar e ativar ambiente virtual (opcional, mas recomendado)

bash
Copiar código
python -m venv venv
source venv/bin/activate    # Linux / macOS  
venv\Scripts\activate       # Windows
Instalar dependências

bash
Copiar código
pip install -r requirements.txt
Configurar variáveis de ambiente (se houver, baseado em .env.example)

Executar o servidor / aplicação

bash
Copiar código
python app.py
Acessar o dashboard web (por exemplo, em http://localhost:5000 — ajuste conforme configuração)

🎯 Uso / Fluxo típico
Enviar imagens ou vídeo de motos para o módulo de visão computacional

O módulo classifica modelo e verifica estado de conservação

Dados de sensores IoT (reais ou simulados) alimentam o dashboard

IA generativa gera relatórios, cronogramas ou responde a consultas em linguagem natural

Usuário visualiza no dashboard e pode tomar decisões com base nos insights

🧪 Exemplos / Demonstrações
Exemplo de input de imagem → saída com modelo + classificação de conservação

Exemplo de consulta em linguagem natural (“Quais motos estão críticas?”)

Simulação de sensores com leitura em tempo real no dashboard

📂 Estrutura do repositório
cpp
Copiar código
VisaoComputacionalPython/
│
├── app.py
├── dashboard_iot.py
├── iot_sensors.py
├── motoscan_vision.py
├── motoscan_ai.py
├── mqtt_client.py
├── requirements.txt
├── .env.example
├── static/
├── templates/
└── uploads/
🧩 Tecnologias & Bibliotecas utilizadas
OpenCV / bibliotecas de visão computacional

Framework web (Flask, FastAPI ou similar)

MQTT para comunicação IoT

Modelos de IA / NLP (ex: GPT, LLMs, Transformers)

Front-end básico para dashboard (HTML/CSS/JS)

📈 Possíveis melhorias / extensões
Integração com câmera ao vivo (streaming)

Conectividade com sensores físicos (hardware real)

Melhora nos modelos de visão (treinamento customizado com mais dados)

Interface de usuário mais robusta

Autenticação / permissões de acesso

API REST para integração com sistemas externos




