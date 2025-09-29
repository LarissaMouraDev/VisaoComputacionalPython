# 🏗️ Arquitetura do Sistema MotoScan

## 📐 Visão Geral da Arquitetura

O MotoScan é construído com uma arquitetura modular que integra três tecnologias disruptivas:

## 🧩 Componentes Principais

### 1. **Frontend (Interface Web)**
**Arquivo:** `templates/index.html`  
**Tecnologias:** HTML5, CSS3, JavaScript, Chart.js

**Funcionalidades:**
- Upload e preview de imagens
- Visualização de resultados em abas
- Dashboard IoT interativo
- Consultas à IA em linguagem natural
- Interface responsiva

### 2. **Backend API (Flask)**
**Arquivo:** `app.py`  
**Tecnologias:** Python 3.8+, Flask, Threading

**Endpoints Principais:**
- `POST /upload` - Upload e análise de imagens
- `GET /api/iot/data` - Dados IoT em tempo real
- `POST /api/ai/ask` - Consultas à IA
- `POST /api/mqtt/publish` - Publicação MQTT
- `GET /iot/dashboard` - Dashboard IoT

### 3. **Módulo de Visão Computacional**
**Arquivo:** `motoscan_vision.py`  
**Tecnologias:** OpenCV, NumPy, Algoritmos Customizados

**Técnicas Utilizadas:**
1. **Conversão de Espaço de Cores:** BGR → HSV para melhor detecção
2. **Detecção de Verde Mottu:** Múltiplas máscaras para capturar variações
3. **Análise de Bordas:** Algoritmo Canny para detectar contornos
4. **Detecção de Círculos:** Hough Transform para identificar rodas
5. **Análise de Textura:** Filtros para avaliar superfícies
6. **Scoring Multicritério:** Pontuação para cada modelo

**Modelos Suportados:**
- **Mottu Pop:** Verde vibrante, maior contraste
- **Mottu Sport 110i:** Design esportivo, mais bordas
- **Mottu E:** Formato scooter, menos bordas definidas

