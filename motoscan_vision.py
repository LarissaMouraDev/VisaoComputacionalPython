import cv2
import numpy as np

def detect_motorcycle(image_path, weights_path='models/yolov3.weights', 
                     config_path='models/yolov3.cfg', 
                     names_path='models/coco.names'):
    """
    Detecta motocicletas em uma imagem usando YOLO
    """
    # Carregar YOLO
    net = cv2.dnn.readNet(weights_path, config_path)
    
    # Carregar classes
    with open(names_path, 'r') as f:
        classes = [line.strip() for line in f.readlines()]
    
    # Carregar imagem
    image = cv2.imread(image_path)
    height, width = image.shape[:2]
    
    # Preparar imagem para YOLO
    blob = cv2.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    
    # Obter camadas de saída
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    
    # Fazer detecção
    outputs = net.forward(output_layers)
    
    # Processar detecções
    motorcycles = []
    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            
            # Verificar se é motocicleta (classe 3 no COCO)
            if class_id == 3 and confidence > 0.5:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                
                motorcycles.append({
                    'confidence': float(confidence),
                    'box': [x, y, w, h]
                })
    
    return motorcycles, image