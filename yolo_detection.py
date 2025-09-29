import cv2
import numpy as np
import os
from datetime import datetime
import json
import urllib.request

class YOLOMotorcycleDetector:
    """
    Detector de motocicletas usando YOLO v3/v4
    """
    
    def __init__(self):
        self.input_folder = "static/images"
        self.output_folder = "static/detections"
        self.models_folder = "models"
        
        os.makedirs(self.input_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.models_folder, exist_ok=True)
        
        self.net = None
        self.classes = []
        self.output_layers = []
        self.colors = []
        
        print("Inicializando detector YOLO...")
        self.setup_yolo()
    
    def download_yolo_files(self):
        """
        Download automático dos arquivos YOLO
        """
        print("\nBaixando arquivos YOLO (isso pode demorar alguns minutos)...")
        
        files = {
            'yolov3.weights': 'https://pjreddie.com/media/files/yolov3.weights',
            'yolov3.cfg': 'https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg',
            'coco.names': 'https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names'
        }
        
        for filename, url in files.items():
            filepath = os.path.join(self.models_folder, filename)
            
            if os.path.exists(filepath):
                print(f"Arquivo {filename} ja existe")
                continue
            
            try:
                print(f"Baixando {filename}...")
                urllib.request.urlretrieve(url, filepath)
                print(f"Download concluido: {filename}")
            except Exception as e:
                print(f"Erro ao baixar {filename}: {e}")
                return False
        
        return True
    
    def setup_yolo(self):
        """
        Configura YOLO
        """
        weights_path = os.path.join(self.models_folder, "yolov3.weights")
        config_path = os.path.join(self.models_folder, "yolov3.cfg")
        names_path = os.path.join(self.models_folder, "coco.names")
        
        # Verificar se arquivos existem
        if not all(os.path.exists(p) for p in [weights_path, config_path, names_path]):
            print("\nArquivos YOLO nao encontrados.")
            print("Opcoes:")
            print("1. Baixar automaticamente (recomendado)")
            print("2. Download manual")
            
            choice = input("Digite sua escolha (1 ou 2): ").strip()
            
            if choice == "1":
                if not self.download_yolo_files():
                    print("\nFalha no download. Instrucoes para download manual:")
                    self.print_download_instructions()
                    return False
            else:
                self.print_download_instructions()
                return False
        
        try:
            # Carregar YOLO
            print("Carregando modelo YOLO...")
            self.net = cv2.dnn.readNet(weights_path, config_path)
            
            # Verificar se GPU está disponível
            if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                print("Usando GPU para processamento")
            else:
                self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
                print("Usando CPU para processamento")
            
            # Obter camadas de saída
            layer_names = self.net.getLayerNames()
            output_layers_indices = self.net.getUnconnectedOutLayers()
            self.output_layers = [layer_names[i - 1] for i in output_layers_indices.flatten()]
            
            # Carregar classes
            with open(names_path, 'r') as f:
                self.classes = [line.strip() for line in f.readlines()]
            
            # Gerar cores para cada classe
            np.random.seed(42)
            self.colors = np.random.randint(0, 255, size=(len(self.classes), 3), dtype='uint8')
            
            print(f"YOLO carregado com sucesso! Classes disponiveis: {len(self.classes)}")
            return True
            
        except Exception as e:
            print(f"Erro ao carregar YOLO: {e}")
            return False
    
    def print_download_instructions(self):
        """
        Instruções para download manual
        """
        print("\n=== DOWNLOAD MANUAL DOS ARQUIVOS YOLO ===")
        print("\n1. YOLOv3 Weights (237 MB):")
        print("   https://pjreddie.com/media/files/yolov3.weights")
        print("   Salve em: models/yolov3.weights")
        
        print("\n2. YOLOv3 Config:")
        print("   https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg")
        print("   Salve em: models/yolov3.cfg")
        
        print("\n3. COCO Names:")
        print("   https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names")
        print("   Salve em: models/coco.names")
        
        print("\nApos baixar os arquivos, execute o script novamente.")
        print("="*50)
    
    def detect_objects(self, image, confidence_threshold=0.5, nms_threshold=0.4):
        """
        Detecta objetos usando YOLO
        """
        if self.net is None:
            return []
        
        height, width, channels = image.shape
        
        # Preparar imagem para YOLO
        blob = cv2.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)
        
        # Fazer predição
        layer_outputs = self.net.forward(self.output_layers)
        
        # Processar detecções
        boxes = []
        confidences = []
        class_ids = []
        
        for output in layer_outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > confidence_threshold:
                    # Coordenadas do objeto
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    
                    # Coordenadas do retângulo
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        # Non-Maximum Suppression
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, nms_threshold)
        
        detections = []
        if len(indexes) > 0:
            for i in indexes.flatten():
                x, y, w, h = boxes[i]
                class_id = class_ids[i]
                confidence = confidences[i]
                class_name = self.classes[class_id]
                
                detections.append({
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': [x, y, w, h]
                })
        
        return detections
    
    def filter_motorcycles(self, detections):
        """
        Filtra apenas motocicletas e bicicletas
        """
        motorcycle_classes = ['motorcycle', 'bicycle', 'motorbike']
        filtered = []
        
        for detection in detections:
            if detection['class_name'] in motorcycle_classes:
                filtered.append(detection)
        
        return filtered
    
    def draw_detections(self, image, detections, show_all=False):
        """
        Desenha detecções na imagem
        """
        output_image = image.copy()
        
        for detection in detections:
            x, y, w, h = detection['bbox']
            class_name = detection['class_name']
            confidence = detection['confidence']
            class_id = detection['class_id']
            
            # Cor baseada na classe
            if class_name in ['motorcycle', 'bicycle', 'motorbike']:
                color = (0, 255, 0)  # Verde para motos
            else:
                if not show_all:
                    continue
                color = tuple(map(int, self.colors[class_id]))
            
            # Desenhar retângulo
            cv2.rectangle(output_image, (x, y), (x + w, y + h), color, 2)
            
            # Preparar texto
            label = f"{class_name}: {confidence:.2%}"
            
            # Tamanho do texto
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
            
            # Desenhar fundo do texto
            cv2.rectangle(output_image, 
                         (x, y - text_height - 10), 
                         (x + text_width, y), 
                         color, -1)
            
            # Desenhar texto
            cv2.putText(output_image, label, (x, y - 5), 
                       font, font_scale, (255, 255, 255), thickness)
        
        return output_image
    
    def process_image(self, image_path, save_result=True):
        """
        Processa uma imagem
        """
        if self.net is None:
            print("YOLO nao esta carregado. Execute setup_yolo() primeiro.")
            return None
        
        print(f"\nProcessando: {os.path.basename(image_path)}")
        
        # Ler imagem
        image = cv2.imread(image_path)
        if image is None:
            print(f"Erro ao ler imagem: {image_path}")
            return None
        
        # Detectar objetos
        all_detections = self.detect_objects(image)
        motorcycles = self.filter_motorcycles(all_detections)
        
        print(f"Total de objetos detectados: {len(all_detections)}")
        print(f"Motocicletas detectadas: {len(motorcycles)}")
        
        # Detalhes das motocicletas
        for i, moto in enumerate(motorcycles, 1):
            print(f"  Moto {i}: {moto['class_name']} - Confianca: {moto['confidence']:.2%}")
        
        if save_result:
            # Desenhar todas as detecções (opcional)
            output_all = self.draw_detections(image, all_detections, show_all=True)
            
            # Desenhar apenas motocicletas
            output_motorcycles = self.draw_detections(image, motorcycles, show_all=False)
            
            # Salvar resultados
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            basename = os.path.splitext(os.path.basename(image_path))[0]
            
            output_all_path = os.path.join(self.output_folder, f"{basename}_all_{timestamp}.jpg")
            output_moto_path = os.path.join(self.output_folder, f"{basename}_motos_{timestamp}.jpg")
            
            cv2.imwrite(output_all_path, output_all)
            cv2.imwrite(output_moto_path, output_motorcycles)
            
            print(f"Resultados salvos:")
            print(f"  Todas deteccoes: {output_all_path}")
            print(f"  Apenas motos: {output_moto_path}")
        
        return {
            'image_path': image_path,
            'all_detections': all_detections,
            'motorcycles': motorcycles,
            'motorcycle_count': len(motorcycles)
        }
    
    def process_all_images(self):
        """
        Processa todas as imagens da pasta
        """
        if self.net is None:
            print("YOLO nao carregado. Nao e possivel processar imagens.")
            return
        
        print("\n" + "="*60)
        print("PROCESSAMENTO DE IMAGENS COM YOLO")
        print("="*60)
        
        # Listar imagens
        extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        image_files = [f for f in os.listdir(self.input_folder) 
                      if os.path.splitext(f)[1].lower() in extensions]
        
        if not image_files:
            print(f"\nNenhuma imagem encontrada em {self.input_folder}")
            return
        
        print(f"\nEncontradas {len(image_files)} imagem(ns)")
        print("-"*60)
        
        results = []
        total_motorcycles = 0
        
        for image_file in image_files:
            image_path = os.path.join(self.input_folder, image_file)
            result = self.process_image(image_path)
            
            if result:
                results.append(result)
                total_motorcycles += result['motorcycle_count']
        
        # Resumo
        print("\n" + "="*60)
        print("RESUMO DO PROCESSAMENTO")
        print("="*60)
        print(f"Imagens processadas: {len(results)}")
        print(f"Total de motocicletas detectadas: {total_motorcycles}")
        print(f"Media por imagem: {total_motorcycles/len(results):.1f}")
        print(f"Resultados salvos em: {self.output_folder}")
        print("="*60)
        
        # Salvar JSON
        json_path = "detection_results_yolo.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Dados salvos em: {json_path}")


def main():
    detector = YOLOMotorcycleDetector()
    
    if detector.net is None:
        print("\nNao foi possivel carregar YOLO. Verifique os arquivos.")
        return
    
    print("\n=== OPCOES ===")
    print("1. Processar todas as imagens da pasta static/images")
    print("2. Processar uma imagem especifica")
    print("3. Testar deteccao com imagem de exemplo")
    
    try:
        choice = input("\nEscolha uma opcao (1-3): ").strip()
        
        if choice == "1":
            detector.process_all_images()
        
        elif choice == "2":
            filename = input("Digite o nome do arquivo: ").strip()
            image_path = os.path.join(detector.input_folder, filename)
            
            if os.path.exists(image_path):
                detector.process_image(image_path)
            else:
                print(f"Arquivo nao encontrado: {image_path}")
        
        elif choice == "3":
            # Usar primeira imagem disponível
            extensions = ['.jpg', '.jpeg', '.png', '.bmp']
            image_files = [f for f in os.listdir(detector.input_folder) 
                          if os.path.splitext(f)[1].lower() in extensions]
            
            if image_files:
                test_image = os.path.join(detector.input_folder, image_files[0])
                detector.process_image(test_image)
            else:
                print("Nenhuma imagem encontrada para teste")
        
        else:
            print("Opcao invalida")
    
    except KeyboardInterrupt:
        print("\nOperacao cancelada")
    except Exception as e:
        print(f"Erro: {e}")


if __name__ == "__main__":
    main()