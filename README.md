# 🚀 Sistema IoT - Instruções de Execução

## ✅ Pré-requisitos Confirmados

Você já tem:
- ✅ Python instalado
- ✅ Ambiente virtual criado (`iot_env`)
- ✅ Dependências básicas instaladas

## 📁 Estrutura de Arquivos Necessária

Crie esta estrutura de pastas no seu projeto:

```
VisaoComputacionalPython/
├── main.py                 (código completo fornecido)
├── templates/
│   └── dashboard.html      (interface web fornecida)
├── iot_env/               (ambiente virtual existente)
└── iot_motorcycle_data.db (será criado automaticamente)
```

## 🛠️ Passos de Execução

### 1. Ativar Ambiente Virtual
```bash
iot_env\Scripts\activate
```

### 2. Criar Pasta Templates
```bash
mkdir templates
```

### 3. Salvar Arquivos
- Copie o código `main.py` completo
- Copie o código `dashboard.html` na pasta `templates/`

### 4. Executar o Sistema
```bash
python main.py
```

### 5. Escolher Modo de Operação
Quando executar, você verá:
```
Escolha o modo de execução:
1. Sistema IoT Completo (com Flask)
2. Sistema IoT Simplificado (apenas terminal)
```

**Recomendação:** Digite `1` para o sistema completo

## 🌐 Acessar Dashboard

Após iniciar, abra no navegador:
- **Local:** http://127.0.0.1:5000
- **Rede:** http://192.168.0.7:5000

## 📊 O que Você Verá

### No Terminal:
```
Sistema IoT de Detecção de Motocicletas inicializado
Banco de dados configurado com sucesso
Sistema IoT iniciado com sucesso
Iniciando dashboard web em http://localhost:5000
Sensor temperature: 28.8
Sensor humidity: 72.6
Sensor motion: False
Sensor light: 341.1
```

### No Dashboard Web:
- 📊 Gráficos em tempo real
- 🌡️ Temperatura, umidade, movimento, luz
- 🏍️ Contador de motocicletas
- 📈 Histórico de dados
- ⚡ Controles do sistema

## 🎯 Funcionalidades Disponíveis

### ✅ Sensores IoT (4 tipos):
- **Temperatura:** Simulação realística com variação diária
- **Umidade:** Correlacionada com temperatura
- **Movimento:** Detecção probabilística
- **Luminosidade:** Baseada na hora do dia

### ✅ Detecção de Motocicletas:
- **Simulação inteligente:** Detecta quando há movimento
- **Múltiplas detecções:** 1-3 motocicletas por vez
- **Níveis de confiança:** 60-95%

### ✅ Dashboard Web:
- **Tempo real:** Atualização a cada 2 segundos
- **Gráficos dinâmicos:** Chart.js com histórico
- **Alertas automáticos:** Temperatura/umidade alta
- **Exportação:** Dados em CSV
- **Responsivo:** Funciona em mobile

### ✅ Banco de Dados:
- **SQLite:** Persistência automática
- **Duas tabelas:** Sensores e detecções
- **Histórico completo:** Todas as leituras salvas

## 🔧 Controles Disponíveis

### No Dashboard:
- 🎯 **Pausar/Ativar Sistema**
- 📊 **Exportar Dados** (CSV)
- 🗑️ **Limpar Histórico**

### No Terminal:
- **Ctrl+C:** Parar sistema
- **Dados em tempo real:** Logs contínuos

## 📈 Métricas Monitoradas

### Estatísticas em Tempo Real:
- **Total de Leituras:** Contador de dados coletados
- **Total de Detecções:** Motocicletas identificadas
- **Temperatura Média:** Cálculo dinâmico
- **Tempo Online:** Uptime do sistema

### Alertas Automáticos:
- 🔥 **Temperatura > 35°C**
- 💧 **Umidade > 80%**
- 🏍️ **Múltiplas motocicletas (>3)**
- 🌙 **Baixa luminosidade (<100 lux)**

## ⚠️ Resolução de Problemas

### Se der erro 500 no navegador:
1. Verificar se `templates/dashboard.html` existe
2. Parar e reiniciar o sistema

### Se não aparecer dados:
1. Aguardar 2-3 segundos para primeira leitura
2. Verificar console do navegador (F12)

### Se der erro de dependências:
1. Ativar ambiente virtual
2. Reinstalar: `pip install flask flask-socketio numpy`

## 🎯 Casos de Teste Implementados

O sistema simula automaticamente:

### 1. **Cenário Normal** (60% do tempo)
- Temperatura: 20-30°C
- Movimento esporádico
- Motocicletas ocasionais

### 2. **Cenário Noturno** (22h-6h)
- Baixa luminosidade
- Menos movimento
- Temperatura reduzida

### 3. **Cenário de Alto Tráfego** (aleatório)
- Movimento constante
- Múltiplas detecções
- Alertas ativados

## 📋 Checklist de Funcionamento

Verifique se tem:
- ✅ Sistema iniciando sem erros
- ✅ Dados de sensores aparecendo no terminal
- ✅ Dashboard carregando no navegador
- ✅ Gráficos atualizando em tempo real
- ✅ Contador de detecções funcionando
- ✅ Botões de controle responsivos

## 🎉 Sistema Funcionando!

Se tudo estiver ok, você terá um **sistema IoT completo** com:
- 📡 4 sensores distintos operando
- 🔄 Comunicação em tempo real
- 📊 Dashboard web moderno
- 🗄️ Persistência de dados
- 🏍️ Detecção de motocicletas
- 📈 Análise e exportação

**Parabéns! Seu projeto IoT está 100% operacional!** 🚀