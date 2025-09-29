import paho.mqtt.client as mqtt
import json
import time
import random
import threading
from datetime import datetime

class MQTTSensorSimulator:
    """
    Simulador de sensores IoT que publica dados via MQTT
    Simula 3 sensores distintos conforme requisitos do projeto
    """
    
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client()
        self.running = False
        
        # Configuração dos sensores
        self.sensors = {
            'temperature': {
                'topic': 'sensors/temperature',
                'min_value': 15,
                'max_value': 40,
                'current_value': 25,
                'variation': 2,
                'unit': '°C'
            },
            'humidity': {
                'topic': 'sensors/humidity', 
                'min_value': 30,
                'max_value': 90,
                'current_value': 60,
                'variation': 5,
                'unit': '%'
            },
            'motion': {
                'topic': 'sensors/motion',
                'min_value': 0,
                'max_value': 1,
                'current_value': 0,
                'variation': 1,
                'unit': 'boolean'
            },
            'light': {
                'topic': 'sensors/light',
                'min_value': 50,
                'max_value': 1000,
                'current_value': 300,
                'variation': 50,
                'unit': 'lux'
            }
        }
        
        # Configurar callbacks MQTT
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback quando conecta ao broker MQTT"""
        if rc == 0:
            print(f" Conectado ao broker MQTT {self.broker_host}:{self.broker_port}")
        else:
            print(f" Falha na conexão MQTT. Código: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback quando desconecta do broker"""
        print(" Desconectado do broker MQTT")
    
    def on_publish(self, client, userdata, mid):
        """Callback quando mensagem é publicada"""
        pass  # Pode ser usado para logging detalhado
    
    def generate_realistic_value(self, sensor_name):
        """Gera valores realistas para cada sensor"""
        sensor = self.sensors[sensor_name]
        
        if sensor_name == 'motion':
            # Sensor de movimento: maior probabilidade de não detectar movimento
            return random.choice([0, 0, 0, 0, 1])  # 20% chance de movimento
        
        elif sensor_name == 'temperature':
            # Temperatura com variação gradual e ciclos diários
            hour = datetime.now().hour
            base_temp = 20 + 10 * (1 + 0.5 * np.sin((hour - 6) * np.pi / 12))
            variation = random.uniform(-sensor['variation'], sensor['variation'])
            value = base_temp + variation
            
        elif sensor_name == 'humidity':
            # Umidade inversamente relacionada à temperatura
            temp = self.sensors['temperature']['current_value']
            base_humidity = 80 - (temp - 20) * 2
            variation = random.uniform(-sensor['variation'], sensor['variation'])
            value = base_humidity + variation
            
        elif sensor_name == 'light':
            # Luminosidade baseada na hora do dia
            hour = datetime.now().hour
            if 6 <= hour <= 18:  # Dia
                base_light = 200 + 600 * (1 + 0.8 * np.sin((hour - 6) * np.pi / 12))
            else:  # Noite
                base_light = random.uniform(50, 150)
            
            variation = random.uniform(-sensor['variation'], sensor['variation'])
            value = base_light + variation
        
        else:
            # Valor padrão com variação aleatória
            current = sensor['current_value']
            variation = random.uniform(-sensor['variation'], sensor['variation'])
            value = current + variation
        
        # Aplicar limites min/max
        value = max(sensor['min_value'], min(sensor['max_value'], value))
        sensor['current_value'] = value
        
        return round(value, 2) if sensor_name != 'motion' else int(value)
    
    def create_message(self, sensor_name, value):
        """Cria mensagem padronizada para MQTT"""
        return {
            'sensor_id': f"sensor_{sensor_name}_001",
            'sensor_type': sensor_name,
            'value': value,
            'unit': self.sensors[sensor_name]['unit'],
            'timestamp': datetime.now().isoformat(),
            'location': {
                'zone': 'parking_lot_entrance',
                'coordinates': [-23.5505, -46.6333]  # São Paulo
            },
            'status': 'online',
            'battery_level': random.randint(80, 100) if sensor_name != 'light' else None
        }
    
    def publish_sensor_data(self, sensor_name):
        """Publica dados de um sensor específico"""
        try:
            value = self.generate_realistic_value(sensor_name)
            message = self.create_message(sensor_name, value)
            
            topic = self.sensors[sensor_name]['topic']
            payload = json.dumps(message, ensure_ascii=False)
            
            result = self.client.publish(topic, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f" {sensor_name.capitalize()}: {value} {self.sensors[sensor_name]['unit']}")
            else:
                print(f" Erro ao publicar {sensor_name}: {result.rc}")
                
        except Exception as e:
            print(f" Erro ao gerar dados do sensor {sensor_name}: {e}")
    
    def simulate_sensor_failure(self, sensor_name, duration=30):
        """Simula falha temporária de um sensor"""
        print(f" Simulando falha do sensor {sensor_name} por {duration} segundos")
        
        # Publicar status de falha
        failure_message = {
            'sensor_id': f"sensor_{sensor_name}_001",
            'sensor_type': sensor_name,
            'status': 'offline',
            'error': 'communication_timeout',
            'timestamp': datetime.now().isoformat()
        }
        
        topic = f"sensors/{sensor_name}/status"
        self.client.publish(topic, json.dumps(failure_message), qos=1)
        
        # Aguardar e restaurar
        time.sleep(duration)
        
        recovery_message = {
            'sensor_id': f"sensor_{sensor_name}_001",
            'sensor_type': sensor_name,
            'status': 'online',
            'timestamp': datetime.now().isoformat()
        }
        
        self.client.publish(topic, json.dumps(recovery_message), qos=1)
        print(f" Sensor {sensor_name} recuperado")
    
    def sensor_worker(self, sensor_name, interval):
        """Worker thread para um sensor específico"""
        failure_chance = 0.001  # 0.1% chance de falha por ciclo
        
        while self.running:
            try:
                # Verificar se deve simular falha
                if random.random() < failure_chance:
                    self.simulate_sensor_failure(sensor_name, random.randint(10, 60))
                
                # Publicar dados normais
                self.publish_sensor_data(sensor_name)
                
                # Aguardar próximo ciclo
                time.sleep(interval)
                
            except Exception as e:
                print(f" Erro no worker do sensor {sensor_name}: {e}")
                time.sleep(interval)
    
    def start_simulation(self):
        """Inicia a simulação de todos os sensores"""
        try:
            # Conectar ao broker
            print(f" Conectando ao broker MQTT {self.broker_host}:{self.broker_port}...")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            time.sleep(2)  # Aguardar conexão
            
            self.running = True
            
            # Criar threads para cada sensor com intervalos diferentes
            sensor_intervals = {
                'temperature': 3,  # A cada 3 segundos
                'humidity': 4,     # A cada 4 segundos
                'motion': 1,       # A cada 1 segundo (mais sensível)
                'light': 5         # A cada 5 segundos
            }
            
            threads = []
            for sensor_name, interval in sensor_intervals.items():
                thread = threading.Thread(
                    target=self.sensor_worker,
                    args=(sensor_name, interval),
                    daemon=True
                )
                thread.start()
                threads.append(thread)
                print(f" Sensor {sensor_name} iniciado (intervalo: {interval}s)")
            
            print("\n Simulação iniciada! Pressione Ctrl+C para parar\n")
            
            # Manter programa rodando
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n Parando simulação...")
                self.stop_simulation()
            
        except Exception as e:
            print(f" Erro ao iniciar simulação: {e}")
    
    def stop_simulation(self):
        """Para a simulação"""
        self.running = False
        
        # Publicar mensagens de desconexão para todos os sensores
        for sensor_name in self.sensors:
            offline_message = {
                'sensor_id': f"sensor_{sensor_name}_001",
                'sensor_type': sensor_name,
                'status': 'offline',
                'timestamp': datetime.now().isoformat()
            }
            topic = f"sensors/{sensor_name}/status"
            self.client.publish(topic, json.dumps(offline_message), qos=1)
        
        time.sleep(1)  # Aguardar envio das mensagens
        self.client.loop_stop()
        self.client.disconnect()
        print(" Simulação encerrada")

# Adicionar numpy para funções matemáticas mais precisas
try:
    import numpy as np
except ImportError:
    # Fallback se numpy não estiver disponível
    import math
    class np:
        @staticmethod
        def sin(x):
            return math.sin(x)


class AdvancedMQTTSensorSimulator(MQTTSensorSimulator):
    """
    Versão avançada do simulador com cenários realistas e casos de teste
    """
    
    def __init__(self, broker_host="localhost", broker_port=1883):
        super().__init__(broker_host, broker_port)
        
        # Cenários de teste
        self.test_scenarios = {
            'normal': {'active': True, 'duration': 300},  # 5 minutos normal
            'high_traffic': {'active': False, 'duration': 120},  # 2 minutos tráfego alto
            'night_mode': {'active': False, 'duration': 180},  # 3 minutos modo noturno
            'storm': {'active': False, 'duration': 90},  # 1.5 minutos tempestade
            'maintenance': {'active': False, 'duration': 60}  # 1 minuto manutenção
        }
        
        self.current_scenario = 'normal'
        self.scenario_start_time = time.time()
    
    def update_scenario(self):
        """Atualiza o cenário atual baseado no tempo"""
        current_time = time.time()
        elapsed = current_time - self.scenario_start_time
        
        # Verificar se deve mudar cenário
        if elapsed > self.test_scenarios[self.current_scenario]['duration']:
            # Escolher próximo cenário
            scenarios = ['normal', 'high_traffic', 'night_mode', 'storm']
            weights = [0.6, 0.2, 0.1, 0.1]  # Probabilidades
            
            self.current_scenario = random.choices(scenarios, weights=weights)[0]
            self.scenario_start_time = current_time
            print(f"🎬 Mudando para cenário: {self.current_scenario}")
    
    def generate_realistic_value(self, sensor_name):
        """Gera valores baseados no cenário atual"""
        self.update_scenario()
        
        sensor = self.sensors[sensor_name]
        base_value = super().generate_realistic_value(sensor_name)
        
        # Aplicar modificações baseadas no cenário
        if self.current_scenario == 'high_traffic':
            if sensor_name == 'motion':
                return 1 if random.random() < 0.8 else 0  # 80% chance de movimento
            elif sensor_name == 'light':
                return base_value * 0.7  # Menos luz devido aos veículos
                
        elif self.current_scenario == 'night_mode':
            if sensor_name == 'light':
                return random.uniform(20, 80)  # Muito pouca luz
            elif sensor_name == 'temperature':
                return base_value - 5  # Mais frio à noite
                
        elif self.current_scenario == 'storm':
            if sensor_name == 'humidity':
                return min(95, base_value + 20)  # Umidade muito alta
            elif sensor_name == 'temperature':
                return base_value - 3  # Temperatura menor
            elif sensor_name == 'light':
                return random.uniform(30, 120)  # Pouca luz
                
        return base_value
    
    def create_test_cases(self):
        """Cria casos de teste específicos"""
        test_cases = [
            {
                'name': 'Moto Desaparecida',
                'description': 'Simula motocicleta que some do estacionamento',
                'duration': 30,
                'sensors': {
                    'motion': [1, 1, 1, 0, 0, 0],  # Movimento depois para
                    'light': 'decrease'  # Luz diminui gradualmente
                }
            },
            {
                'name': 'Moto no Lugar Errado',
                'description': 'Motocicleta estacionada em local inadequado',
                'duration': 45,
                'sensors': {
                    'motion': [1, 1, 0, 0, 0, 1, 1],  # Movimento intermitente
                    'temperature': 'increase'  # Temperatura sobe (motor quente)
                }
            },
            {
                'name': 'Múltiplas Detecções',
                'description': 'Várias motocicletas chegando simultaneamente',
                'duration': 60,
                'sensors': {
                    'motion': [1, 1, 1, 1, 1],  # Movimento constante
                    'light': 'variable',  # Luz variável
                    'temperature': 'stable'  # Temperatura estável
                }
            }
        ]
        
        return test_cases
    
    def run_test_case(self, test_case):
        """Executa um caso de teste específico"""
        print(f" Iniciando teste: {test_case['name']}")
        print(f" Descrição: {test_case['description']}")
        
        start_time = time.time()
        duration = test_case['duration']
        
        while time.time() - start_time < duration:
            for sensor_name, pattern in test_case['sensors'].items():
                if isinstance(pattern, list):
                    # Usar padrão específico
                    index = int((time.time() - start_time) / (duration / len(pattern)))
                    if index < len(pattern):
                        value = pattern[index]
                        message = self.create_message(sensor_name, value)
                        topic = self.sensors[sensor_name]['topic']
                        self.client.publish(topic, json.dumps(message), qos=1)
                        
            time.sleep(2)
        
        print(f" Teste '{test_case['name']}' concluído")


def main():
    """Função principal para executar o simulador"""
    print(" Iniciando Simulador MQTT de Sensores IoT")
    print("=" * 50)
    
    # Configurações
    BROKER_HOST = "localhost"  # Altere para seu broker MQTT
    BROKER_PORT = 1883
    
    # Escolher modo de operação
    print("Escolha o modo de operação:")
    print("1. Simulação Normal")
    print("2. Simulação Avançada com Cenários")
    print("3. Executar Casos de Teste")
    
    choice = input("Digite sua escolha (1-3): ").strip()
    
    if choice == "1":
        simulator = MQTTSensorSimulator(BROKER_HOST, BROKER_PORT)
        simulator.start_simulation()
        
    elif choice == "2":
        simulator = AdvancedMQTTSensorSimulator(BROKER_HOST, BROKER_PORT)
        simulator.start_simulation()
        
    elif choice == "3":
        simulator = AdvancedMQTTSensorSimulator(BROKER_HOST, BROKER_PORT)
        
        # Conectar primeiro
        simulator.client.connect(BROKER_HOST, BROKER_PORT, 60)
        simulator.client.loop_start()
        time.sleep(2)
        
        # Executar casos de teste
        test_cases = simulator.create_test_cases()
        for test_case in test_cases:
            response = input(f"\nExecutar teste '{test_case['name']}'? (s/N): ")
            if response.lower() in ['s', 'sim', 'yes', 'y']:
                simulator.run_test_case(test_case)
                time.sleep(5)  # Pausa entre testes
        
        simulator.client.loop_stop()
        simulator.client.disconnect()
        
    else:
        print(" Opção inválida")


if __name__ == "__main__":
    main()