#!/usr/bin/env python3
"""
Script de inicialização do Sistema IoT de Detecção de Motocicletas
Executa todos os componentes de forma coordenada conforme requisitos do projeto
"""

import subprocess
import sys
import time
import threading
import signal
import os
import json
import logging
from datetime import datetime

class SystemLauncher:
    """
    Gerenciador de inicialização e coordenação do sistema completo
    """
    
    def __init__(self):
        self.processes = {}
        self.running = False
        self.setup_logging()
        
        # Verificar dependências
        self.check_dependencies()
        
        # Configurações
        self.load_config()
        
        print("🚀 Sistema IoT de Detecção de Motocicletas")
        print("=" * 50)
        print("📋 Arquiteturas Disruptivas: IoT, IoB & IA Generativa")
        print("👤 Desenvolvido por: Larissa Moura")
        print("🏫 FIAP - 2024")
        print("=" * 50)
    
    def setup_logging(self):
        """Configura logging do launcher"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - LAUNCHER - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('system_launcher.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self):
        """Carrega configurações do sistema"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    self.config = json.load(f)
                self.logger.info("Configurações carregadas com sucesso")
            else:
                self.logger.warning("Arquivo config.json não encontrado, usando padrões")
                self.config = self.get_default_config()
        except Exception as e:
            self.logger.error(f"Erro ao carregar configurações: {e}")
            self.config = self.get_default_config()
    
    def get_default_config(self):
        """Retorna configurações padrão"""
        return {
            "mqtt": {"broker": "localhost", "port": 1883},
            "dashboard": {"host": "0.0.0.0", "port": 5000},
            "detection": {"confidence_threshold": 0.5}
        }
    
    def check_dependencies(self):
        """Verifica dependências do sistema"""
        print("🔍 Verificando dependências...")
        
        required_modules = [
            'cv2', 'numpy', 'flask', 'paho.mqtt.client', 
            'pandas', 'sqlite3', 'socketio'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
                print(f"  ✅ {module}")
            except ImportError:
                missing_modules.append(module)
                print(f"  ❌ {module}")
        
        if missing_modules:
            print(f"\n⚠️ Módulos faltando: {', '.join(missing_modules)}")
            print("Execute: pip install -r requirements.txt")
            sys.exit(1)
        
        print("✅ Todas as dependências estão instaladas!")
    
    def start_mqtt_broker(self):
        """Inicia broker MQTT se necessário"""
        try:
            # Verificar se mosquitto está rodando
            result = subprocess.run(['pgrep', 'mosquitto'], capture_output=True)
            if result.returncode != 0:
                print("🔌 Iniciando broker MQTT...")
                self.processes['mqtt_broker'] = subprocess.Popen(
                    ['mosquitto', '-v'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                time.sleep(2)
                print("✅ Broker MQTT iniciado")
            else:
                print("✅ Broker MQTT já está rodando")
        except FileNotFoundError:
            print("⚠️ Mosquitto não encontrado. Usando simulação interna.")
    
    def start_components(self):
        """Inicia todos os componentes do sistema"""
        components = [
            {
                'name': 'mqtt_simulator',
                'script': 'mqtt_simulator.py',
                'description': 'Simulador de Sensores MQTT',
                'delay': 2
            },
            {
                'name': 'database_manager',
                'script': 'database_manager.py',
                'description': 'Gerenciador de Banco de Dados',
                'delay': 1
            },
            {
                'name': 'main_system',
                'script': 'main.py',
                'description': 'Sistema Principal Integrado',
                'delay': 3
            }
        ]
        
        for component in components:
            print(f"🚀 Iniciando {component['description']}...")
            try:
                self.processes[component['name']] = subprocess.Popen(
                    [sys.executable, component['script']],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                time.sleep(component['delay'])
                print(f"✅ {component['description']} iniciado")
            except Exception as e:
                print(f"❌ Erro ao iniciar {component['description']}: {e}")
    
    def show_status(self):
        """Mostra status dos componentes"""
        print("\n📊 STATUS DOS COMPONENTES")
        print("-" * 30)
        
        for name, process in self.processes.items():
            if process.poll() is None:
                status = "🟢 RODANDO"
            else:
                status = "🔴 PARADO"
            print(f"{name}: {status}")
        
        # URLs importantes
        print("\n🌐 ACESSO AO SISTEMA")
        print("-" * 20)
        dashboard_port = self.config.get('dashboard', {}).get('port', 5000)
        print(f"Dashboard Web: http://localhost:{dashboard_port}")
        print("Controles do sistema:")
        print("  - 'q' + Enter: Sair")
        print("  - 's' + Enter: Status")
        print("  - 'r' + Enter: Reiniciar componentes")
        print("  - 'l' + Enter: Ver logs")
    
    def show_logs(self):
        """Mostra logs recentes do sistema"""
        print("\n📄 LOGS RECENTES")
        print("-" * 20)
        
        log_files = ['system_launcher.log', 'system.log', 'mqtt.log']
        
        for log_file in log_files:
            if os.path.exists(log_file):
                print(f"\n📋 {log_file}:")
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        # Mostrar últimas 5 linhas
                        for line in lines[-5:]:
                            print(f"  {line.strip()}")
                except Exception as e:
                    print(f"  Erro ao ler log: {e}")
    
    def restart_components(self):
        """Reinicia todos os componentes"""
        print("🔄 Reiniciando componentes...")
        self.stop_all()
        time.sleep(3)
        self.start_mqtt_broker()
        self.start_components()
        print("✅ Componentes reiniciados")
    
    def run_interactive_demo(self):
        """Executa demonstração interativa dos casos de teste"""
        print("\n🎯 DEMONSTRAÇÃO INTERATIVA")
        print("=" * 30)
        
        test_cases = [
            {
                'name': 'Moto Desaparecida',
                'description': 'Simula motocicleta que some do estacionamento',
                'duration': 30
            },
            {
                'name': 'Moto no Lugar Errado',
                'description': 'Motocicleta estacionada em local inadequado', 
                'duration': 45
            },
            {
                'name': 'Múltiplas Detecções',
                'description': 'Várias motocicletas chegando simultaneamente',
                'duration': 60
            }
        ]
        
        print("Casos de teste disponíveis:")
        for i, test in enumerate(test_cases, 1):
            print(f"{i}. {test['name']} - {test['description']}")
        
        try:
            choice = input("\nEscolha um caso para demonstrar (1-3) ou Enter para pular: ")
            if choice.isdigit() and 1 <= int(choice) <= 3:
                selected_test = test_cases[int(choice) - 1]
                print(f"\n🧪 Executando: {selected_test['name']}")
                print(f"📋 {selected_test['description']}")
                print(f"⏱️ Duração: {selected_test['duration']} segundos")
                print("🎬 Acompanhe os resultados no dashboard!")
                
                # Aqui você poderia executar o caso de teste específico
                # Por exemplo, enviar comandos MQTT específicos
                
        except (ValueError, KeyboardInterrupt):
            pass
    
    def handle_user_input(self):
        """Manipula entrada do usuário"""
        while self.running:
            try:
                command = input().strip().lower()
                
                if command == 'q':
                    print("🛑 Encerrando sistema...")
                    self.running = False
                    break
                elif command == 's':
                    self.show_status()
                elif command == 'r':
                    self.restart_components()
                elif command == 'l':
                    self.show_logs()
                elif command == 'd':
                    self.run_interactive_demo()
                elif command == 'h':
                    self.show_help()
                    
            except (EOFError, KeyboardInterrupt):
                self.running = False
                break
    
    def show_help(self):
        """Mostra ajuda dos comandos"""
        print("\n❓ COMANDOS DISPONÍVEIS")
        print("-" * 20)
        print("q - Sair do sistema")
        print("s - Mostrar status")
        print("r - Reiniciar componentes")
        print("l - Ver logs recentes")
        print("d - Demonstração interativa")
        print("h - Mostrar esta ajuda")
    
    def stop_all(self):
        """Para todos os processos"""
        for name, process in self.processes.items():
            if process.poll() is None:
                print(f"🛑 Parando {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        self.processes.clear()
    
    def signal_handler(self, signum, frame):
        """Manipula sinais do sistema"""
        self.logger.info(f"Recebido sinal {signum}")
        self.running = False
    
    def run(self):
        """Executa o sistema completo"""
        # Configurar handlers de sinal
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.running = True
        
        try:
            # Iniciar broker MQTT
            self.start_mqtt_broker()
            
            # Iniciar componentes
            self.start_components()
            
            # Mostrar status inicial
            time.sleep(3)
            self.show_status()
            
            # Demonstração interativa opcional
            demo_choice = input("\n🎯 Executar demonstração interativa? (s/N): ")
            if demo_choice.lower() in ['s', 'sim', 'yes', 'y']:
                self.run_interactive_demo()
            
            print("\n💡 Sistema rodando! Digite 'h' para ver comandos disponíveis.")
            
            # Thread para entrada do usuário
            input_thread = threading.Thread(target=self.handle_user_input, daemon=True)
            input_thread.start()
            
            # Loop principal
            while self.running:
                time.sleep(1)
                
                # Verificar se processos ainda estão rodando
                for name, process in list(self.processes.items()):
                    if process.poll() is not None:
                        self.logger.warning(f"Processo {name} parou inesperadamente")
        
        except Exception as e:
            self.logger.error(f"Erro no sistema principal: {e}")
        
        finally:
            print("\n🧹 Limpando recursos...")
            self.stop_all()
            print("✅ Sistema encerrado com sucesso!")


def main():
    """Função principal"""
    launcher = SystemLauncher()
    launcher.run()


if __name__ == "__main__":
    main()