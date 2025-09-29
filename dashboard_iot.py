# Adicione este arquivo como dashboard_iot.py

from flask import Blueprint, render_template, jsonify
import random
import time
from datetime import datetime, timedelta

# Criar um Blueprint para as rotas de IoT
iot_blueprint = Blueprint('iot', __name__)

# Dados simulados para histórico (últimas 24 horas)
def generate_historical_data():
    now = datetime.now()
    data = []
    for i in range(24):
        timestamp = (now - timedelta(hours=23-i)).strftime("%H:%M")
        data.append({
            "timestamp": timestamp,
            "temperatura": round(random.uniform(70, 90), 1),
            "bateria": round(random.uniform(60, 100), 1),
            "combustivel": round(random.uniform(20, 100), 1)
        })
    return data

# Dados de localização para motos Mottu
mottu_locations = [
    {"id": 1, "modelo": "Mottu E", "lat": -23.5505, "lng": -46.6333, "status": "em uso"},
    {"id": 2, "modelo": "Mottu Sport 110i", "lat": -23.5570, "lng": -46.6650, "status": "estacionada"},
    {"id": 3, "modelo": "Mottu Pop", "lat": -23.5480, "lng": -46.6380, "status": "em manutenção"},
    {"id": 4, "modelo": "Mottu E", "lat": -23.5420, "lng": -46.6290, "status": "em uso"},
    {"id": 5, "modelo": "Mottu Sport 110i", "lat": -23.5550, "lng": -46.6400, "status": "estacionada"}
]

# Rota para o dashboard principal de IoT
@iot_blueprint.route('/dashboard')
def dashboard():
    return render_template('iot_dashboard.html')

# API para obter dados históricos
@iot_blueprint.route('/api/historical')
def historical_data():
    return jsonify(generate_historical_data())

# API para obter localização das motos
@iot_blueprint.route('/api/locations')
def locations():
    # Adicionar pequena variação para simular movimento
    for moto in mottu_locations:
        if moto["status"] == "em uso":
            moto["lat"] += random.uniform(-0.0005, 0.0005)
            moto["lng"] += random.uniform(-0.0005, 0.0005)
    return jsonify(mottu_locations)

# API para obter alertas recentes
@iot_blueprint.route('/api/alerts')
def alerts():
    alert_types = [
        "Temperatura elevada",
        "Bateria baixa",
        "Movimento não autorizado",
        "Manutenção necessária",
        "Combustível baixo"
    ]
    
    # Gerar 0-3 alertas aleatórios
    num_alerts = random.randint(0, 3)
    alerts = []
    
    for i in range(num_alerts):
        alerts.append({
            "tipo": random.choice(alert_types),
            "moto_id": random.randint(1, 5),
            "modelo": random.choice(["Mottu E", "Mottu Sport 110i", "Mottu Pop"]),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "severidade": random.choice(["baixa", "média", "alta"])
        })
    
    return jsonify(alerts)