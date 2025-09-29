import cv2
import numpy as np
import threading
import time
import json
import sqlite3
from datetime import datetime
import random
import os
from flask import Flask, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import logging

class IoTMotorcycleDetector:
    def __init__(self):
        self.setup_database()
        
        self.sensors_data = {
            'temperature': 25.0,
            'humidity': 60.0,
            'motion': False,
            'light': 300,
            'motorcycles_detected': 0,
            'last_detection': None
        }
        
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'secret_key_iot'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.setup_flask_routes()
        
        self.running = False
        self.detection_active = True
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.setup_detector()
        self.create_directories()
        
        print("Sistema IoT de Detecao de Motocicletas inicializado")
    
    def create_directories(self):
        directories = ['static', 'static/images', 'static/detections', 'models']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def setup_detector(self):
        self.net = None
        self.classes = []
        self.output_layers = []
        
        # ALTERADO: Usando YOLOv3 ao invés de YOLOv4
        weights_path = "models/yolov3.weights"
        config_path = "models/yolov3.cfg"
        names_path = "models/coco.names"
        
        if os.path.exists(weights_path) and os.path.exists(config_path):
            try:
                print("Carregando modelo YOLOv3...")
                self.net = cv2.dnn.readNet(weights_path, config_path)
                
                if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                    self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                    self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                    print("✓ Usando aceleracao GPU")
                else:
                    self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                    self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
                    print("✓ Usando CPU")
                
                layer_names = self.net.getLayerNames()
                # Correção para compatibilidade com diferentes versões do OpenCV
                try:
                    self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
                except:
                    self.output_layers = [layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
                
                if os.path.exists(names_path):
                    with open(names_path, 'r') as f:
                        self.classes = [line.strip() for line in f.readlines()]
                
                print("✓ Modelo YOLOv3 carregado com sucesso!")
                print(f"✓ {len(self.classes)} classes carregadas")
                
            except Exception as e:
                print(f"✗ Erro ao carregar YOLO: {e}")
                self.net = None
        else:
            print("✗ Arquivos YOLO nao encontrados")
            print(f"  Procurado em: {weights_path}")
            print("  Usando detector alternativo (baseado em contornos)")
    
    def setup_database(self):
        self.conn = sqlite3.connect('iot_motorcycle_data.db', check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                temperature REAL,
                humidity REAL,
                motion INTEGER,
                light_level REAL,
                motorcycles_count INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS motorcycle_detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                confidence REAL,
                bbox_x INTEGER,
                bbox_y INTEGER,
                bbox_width INTEGER,
                bbox_height INTEGER,
                image_path TEXT,
                detection_type TEXT
            )
        ''')
        
        self.conn.commit()
        print("✓ Banco de dados configurado com sucesso")
    
    def setup_flask_routes(self):
        
        @self.app.route('/')
        def index():
            return render_template('dashboard.html')
        
        @self.app.route('/api/sensors')
        def get_sensors():
            return jsonify(self.sensors_data)
        
        @self.app.route('/api/history')
        def get_history():
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT timestamp, temperature, humidity, motion, light_level, motorcycles_count 
                FROM sensor_data 
                ORDER BY timestamp DESC 
                LIMIT 50
            ''')
            data = cursor.fetchall()
            
            history = []
            for row in data:
                history.append({
                    'timestamp': row[0],
                    'temperature': row[1],
                    'humidity': row[2],
                    'motion': row[3],
                    'light_level': row[4],
                    'motorcycles_count': row[5]
                })
            
            return jsonify(history)
        
        @self.app.route('/api/detections')
        def get_detections():
            """Retorna lista de imagens detectadas"""
            detections_dir = 'static/detections'
            if not os.path.exists(detections_dir):
                return jsonify([])
            
            images = []
            for filename in os.listdir(detections_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    filepath = os.path.join(detections_dir, filename)
                    timestamp = datetime.fromtimestamp(os.path.getmtime(filepath))
                    images.append({
                        'filename': filename,
                        'timestamp': timestamp.strftime('%d/%m/%Y %H:%M:%S'),
                        'path': f'/static/detections/{filename}'
                    })
            
            # Ordenar por data (mais recente primeiro)
            images.sort(key=lambda x: x['timestamp'], reverse=True)
            return jsonify(images)
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            return send_from_directory('static', filename)
    
    def detect_motorcycles_simple(self, frame):
        """Detector alternativo baseado em contornos (fallback)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if 1000 < area < 50000:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                if 0.8 < aspect_ratio < 3.0:
                    detections.append({
                        'bbox': [x, y, w, h],
                        'confidence': 0.7,
                        'class': 'vehicle',
                        'center': [x + w//2, y + h//2]
                    })
        
        return detections
    
    def detect_motorcycles(self, frame):
        """Método principal de detecção"""
        if self.net is not None:
            return self.detect_motorcycles_yolo(frame)
        else:
            return self.detect_motorcycles_simple(frame)
    
    def detect_motorcycles_yolo(self, frame):
        """Detecção usando YOLOv3"""
        if self.net is None:
            return []
        
        height, width, channels = frame.shape
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.output_layers)
        
        class_ids = []
        confidences = []
        boxes = []
        
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                # Classe 3 = motorcycle, Classe 1 = bicycle no COCO
                if confidence > 0.5 and class_id in [1, 3]:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        
        detections = []
        if len(indexes) > 0:
            for i in indexes.flatten():
                x, y, w, h = boxes[i]
                confidence = confidences[i]
                class_name = self.classes[class_ids[i]] if class_ids[i] < len(self.classes) else "vehicle"
                
                detections.append({
                    'bbox': [x, y, w, h],
                    'confidence': confidence,
                    'class': class_name,
                    'center': [x + w//2, y + h//2]
                })
        
        return detections
    
    def save_detection_data(self, detections, image_filename=""):
        """Salva dados das detecções no banco de dados"""
        try:
            cursor = self.conn.cursor()
            
            for detection in detections:
                bbox = detection['bbox']
                cursor.execute('''
                    INSERT INTO motorcycle_detections 
                    (confidence, bbox_x, bbox_y, bbox_width, bbox_height, detection_type, image_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    detection['confidence'], 
                    bbox[0], bbox[1], bbox[2], bbox[3],
                    detection['class'],
                    image_filename
                ))
            
            self.conn.commit()
        except Exception as e:
            print(f"✗ Erro ao salvar detecao: {e}")
    
    def process_static_images(self):
        """Processa todas as imagens da pasta static/images"""
        images_dir = "static/images"
        
        if not os.path.exists(images_dir):
            print(f"✗ Pasta {images_dir} nao encontrada")
            return
        
        image_files = [f for f in os.listdir(images_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        
        if not image_files:
            print("✗ Nenhuma imagem encontrada na pasta static/images")
            return
        
        print(f"\n{'='*60}")
        print(f"PROCESSAMENTO DE IMAGENS COM YOLO")
        print(f"{'='*60}")
        print(f"Total de imagens encontradas: {len(image_files)}")
        print(f"{'='*60}\n")
        
        total_detections = 0
        processed_count = 0
        
        for idx, image_file in enumerate(image_files, 1):
            image_path = os.path.join(images_dir, image_file)
            
            try:
                print(f"[{idx}/{len(image_files)}] Processando: {image_file}...", end=" ")
                
                frame = cv2.imread(image_path)
                if frame is None:
                    print("✗ Erro ao ler imagem")
                    continue
                
                detections = self.detect_motorcycles(frame)
                
                if detections:
                    total_detections += len(detections)
                    processed_count += 1
                    print(f"✓ {len(detections)} motocicleta(s) detectada(s)")
                    
                    self.save_detection_data(detections, image_file)
                    
                    # Desenhar as detecções
                    for detection in detections:
                        x, y, w, h = detection['bbox']
                        confidence = detection['confidence']
                        class_name = detection['class']
                        
                        # Caixa verde
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        
                        # Label com fundo
                        label = f"{class_name}: {confidence:.2%}"
                        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                        cv2.rectangle(frame, (x, y - label_h - 10), (x + label_w, y), (0, 255, 0), -1)
                        cv2.putText(frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                    
                    # Salvar imagem com detecções
                    output_path = os.path.join("static/detections", f"detection_{image_file}")
                    cv2.imwrite(output_path, frame)
                else:
                    print("○ Nenhuma detecao")
                    
            except Exception as e:
                print(f"✗ Erro: {e}")
        
        print(f"\n{'='*60}")
        print(f"RESUMO DO PROCESSAMENTO")
        print(f"{'='*60}")
        print(f"Imagens processadas: {processed_count}/{len(image_files)}")
        print(f"Total de deteccoes: {total_detections}")
        print(f"Resultados salvos em: static/detections/")
        print(f"{'='*60}\n")
        
        # Atualizar dados dos sensores
        self.sensors_data['motorcycles_detected'] = total_detections
        if total_detections > 0:
            self.sensors_data['last_detection'] = datetime.now().isoformat()
    
    def simulate_sensors(self):
        """Simula leitura de sensores IoT"""
        while self.running:
            hour = datetime.now().hour
            
            # Temperatura
            base_temp = 20 + 10 * (1 + 0.5 * np.sin((hour - 6) * np.pi / 12))
            self.sensors_data['temperature'] = round(base_temp + random.uniform(-3, 3), 1)
            
            # Umidade
            base_humidity = 80 - (self.sensors_data['temperature'] - 20) * 2
            self.sensors_data['humidity'] = round(max(30, min(90, base_humidity + random.uniform(-10, 10))), 1)
            
            # Movimento
            if 6 <= hour <= 22:
                motion_prob = 0.3
            else:
                motion_prob = 0.1
            self.sensors_data['motion'] = random.random() < motion_prob
            
            # Luminosidade
            if 6 <= hour <= 18:
                base_light = 200 + 600 * (1 + 0.8 * np.sin((hour - 6) * np.pi / 12))
            else:
                base_light = random.uniform(50, 150)
            self.sensors_data['light'] = round(max(10, base_light + random.uniform(-50, 50)), 1)
            
            # Salvar no banco
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO sensor_data 
                (temperature, humidity, motion, light_level, motorcycles_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                self.sensors_data['temperature'],
                self.sensors_data['humidity'],
                int(self.sensors_data['motion']),
                self.sensors_data['light'],
                self.sensors_data['motorcycles_detected']
            ))
            self.conn.commit()
            
            # Emitir para dashboard
            self.socketio.emit('sensor_update', self.sensors_data)
            
            time.sleep(2)
    
    def run(self):
        print("\n" + "="*60)
        print("SISTEMA IoT DE DETECCAO DE MOTOCICLETAS")
        print("="*60)
        
        self.running = True
        
        print("\nEscolha o modo de detecao:")
        print("1. Webcam em tempo real")
        print("2. Processar imagens da pasta static/images")
        print("3. Apenas sensores (sem detecao visual)")
        
        try:
            detection_choice = input("\nDigite sua escolha (1-3): ").strip()
        except:
            detection_choice = "3"
        
        # Iniciar thread de sensores
        sensor_thread = threading.Thread(target=self.simulate_sensors, daemon=True)
        sensor_thread.start()
        print("\n✓ Thread de sensores iniciada")
        
        # Processar imagens se escolhido
        if detection_choice == "2":
            self.process_static_images()
            print("✓ Processamento de imagens concluido")
        else:
            print("✓ Modo apenas sensores ativado")
        
        print("\n" + "="*60)
        print("Dashboard web disponivel em: http://localhost:5000")
        print("Pressione Ctrl+C para encerrar")
        print("="*60 + "\n")
        
        try:
            self.socketio.run(self.app, host='0.0.0.0', port=5000, debug=False)
        except KeyboardInterrupt:
            print("\n\nEncerrando sistema...")
            self.running = False
            self.conn.close()
            print("✓ Sistema encerrado com sucesso")


class SimpleIoTSystem:
    """Sistema IoT simplificado sem interface web"""
    def __init__(self):
        self.sensors = {
            'temperature': 25.0,
            'humidity': 60.0,
            'motion': False,
            'light': 300.0,
            'motorcycles': 0
        }
        self.running = True
        
        self.conn = sqlite3.connect('simple_iot.db')
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                sensor_type TEXT,
                value REAL
            )
        ''')
        self.conn.commit()
    
    def update_sensors(self):
        while self.running:
            self.sensors['temperature'] = round(20 + random.uniform(-5, 10), 1)
            self.sensors['humidity'] = round(40 + random.uniform(-20, 40), 1)
            self.sensors['motion'] = random.choice([True, False])
            self.sensors['light'] = round(200 + random.uniform(-100, 300), 1)
            
            if self.sensors['motion']:
                self.sensors['motorcycles'] = random.randint(1, 3)
            else:
                self.sensors['motorcycles'] = 0
            
            timestamp = datetime.now().isoformat()
            cursor = self.conn.cursor()
            for sensor_type, value in self.sensors.items():
                if sensor_type != 'motion':
                    cursor.execute(
                        'INSERT INTO readings (timestamp, sensor_type, value) VALUES (?, ?, ?)',
                        (timestamp, sensor_type, float(value))
                    )
            self.conn.commit()
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Dados IoT:")
            print(f"  Temperatura: {self.sensors['temperature']}°C")
            print(f"  Umidade: {self.sensors['humidity']}%")
            print(f"  Movimento: {'Detectado' if self.sensors['motion'] else 'Nenhum'}")
            print(f"  Luminosidade: {self.sensors['light']} lux")
            print(f"  Motocicletas: {self.sensors['motorcycles']}")
            
            time.sleep(3)
    
    def run(self):
        print("\n" + "="*60)
        print("SISTEMA IoT SIMPLIFICADO")
        print("="*60)
        print("Pressione Ctrl+C para parar\n")
        
        try:
            self.update_sensors()
        except KeyboardInterrupt:
            print("\n\nSistema encerrado")
            self.running = False
            self.conn.close()


def main():
    print("\n" + "="*60)
    print("VISAO COMPUTACIONAL + IoT")
    print("Sistema de Deteccao de Motocicletas")
    print("="*60)
    
    print("\nEscolha o modo de execucao:")
    print("1. Sistema IoT Completo (com Flask e detecao YOLO)")
    print("2. Sistema IoT Simplificado (apenas terminal)")
    
    try:
        choice = input("\nDigite sua escolha (1 ou 2): ").strip()
        
        if choice == "1":
            if not os.path.exists('templates'):
                os.makedirs('templates')
                print("\n⚠ Pasta 'templates' criada")
                print("⚠ Adicione o arquivo dashboard.html para visualizar o dashboard web")
            
            detector = IoTMotorcycleDetector()
            detector.run()
            
        elif choice == "2":
            system = SimpleIoTSystem()
            system.run()
            
        else:
            print("\n✗ Opcao invalida. Executando sistema simplificado...")
            system = SimpleIoTSystem()
            system.run()
            
    except KeyboardInterrupt:
        print("\n\nSistema encerrado pelo usuario")
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()