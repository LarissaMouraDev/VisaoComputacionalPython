CREATE DATABASE IF NOT EXISTS mottu_tracking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mottu_tracking;

-- TABELA: motos
-- ============================================
CREATE TABLE motos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    placa VARCHAR(10) UNIQUE NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    marca VARCHAR(50) NOT NULL,
    ano INT NOT NULL,
    cor VARCHAR(30),
    numero_chassi VARCHAR(50) UNIQUE,
    status ENUM('disponivel', 'em_uso', 'manutencao', 'inativa') DEFAULT 'disponivel',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    quilometragem DECIMAL(10, 2) DEFAULT 0,
    bateria_percentual INT CHECK (bateria_percentual BETWEEN 0 AND 100),
    observacoes TEXT,
    INDEX idx_status (status),
    INDEX idx_placa (placa)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: localizacoes
-- ============================================
CREATE TABLE localizacoes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    moto_id INT NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    velocidade DECIMAL(5, 2) DEFAULT 0,
    direcao VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    origem_dados ENUM('iot', 'visao_computacional', 'manual', 'gps') DEFAULT 'iot',
    precisao DECIMAL(5, 2),
    altitude DECIMAL(8, 2),
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE CASCADE,
    INDEX idx_moto_timestamp (moto_id, timestamp),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: areas_patio
-- ============================================
CREATE TABLE areas_patio (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    tipo ENUM('estacionamento', 'manutencao', 'carga', 'entrada', 'saida', 'restrita'),
    capacidade INT,
    coordenadas_poligono JSON,
    descricao TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================
-- TABELA: motos_areas
-- ============================================
CREATE TABLE motos_areas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    moto_id INT NOT NULL,
    area_id INT NOT NULL,
    entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    saida TIMESTAMP NULL,
    duracao_minutos INT AS (TIMESTAMPDIFF(MINUTE, entrada, saida)) STORED,
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE CASCADE,
    FOREIGN KEY (area_id) REFERENCES areas_patio(id) ON DELETE CASCADE,
    INDEX idx_moto_periodo (moto_id, entrada, saida)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: alertas
-- ============================================
CREATE TABLE alertas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    moto_id INT,
    tipo ENUM('bateria_baixa', 'manutencao_necessaria', 'velocidade_alta', 
              'area_nao_autorizada', 'inatividade', 'colisao', 
              'roubo_suspeito', 'sensor_offline', 'outro') NOT NULL,
    severidade ENUM('baixa', 'media', 'alta', 'critica') DEFAULT 'media',
    mensagem TEXT NOT NULL,
    detalhes JSON,
    resolvido BOOLEAN DEFAULT FALSE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_resolucao TIMESTAMP NULL,
    resolvido_por VARCHAR(100),
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE SET NULL,
    INDEX idx_moto_alertas (moto_id, data_criacao),
    INDEX idx_nao_resolvidos (resolvido, data_criacao),
    INDEX idx_tipo_severidade (tipo, severidade, resolvido)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: manutencoes
-- ============================================
CREATE TABLE manutencoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    moto_id INT NOT NULL,
    tipo ENUM('preventiva', 'corretiva', 'revisao', 'troca_oleo', 
              'troca_pneu', 'freios', 'eletrica', 'bateria', 'outra') NOT NULL,
    descricao TEXT NOT NULL,
    custo DECIMAL(10, 2),
    data_inicio TIMESTAMP NOT NULL,
    data_conclusao TIMESTAMP NULL,
    status ENUM('agendada', 'em_andamento', 'concluida', 'cancelada') DEFAULT 'agendada',
    mecanico VARCHAR(100),
    observacoes TEXT,
    proxima_manutencao DATE,
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE CASCADE,
    INDEX idx_moto_manutencao (moto_id, data_inicio)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: entregadores
-- ============================================
CREATE TABLE entregadores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    cnh VARCHAR(20) UNIQUE NOT NULL,
    categoria_cnh VARCHAR(5),
    telefone VARCHAR(20),
    email VARCHAR(100) UNIQUE,
    status ENUM('ativo', 'inativo', 'suspenso', 'ferias') DEFAULT 'ativo',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    avaliacao DECIMAL(3, 2) CHECK (avaliacao BETWEEN 0 AND 5),
    total_entregas INT DEFAULT 0,
    INDEX idx_cpf (cpf),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: viagens
-- ============================================
CREATE TABLE viagens (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    moto_id INT NOT NULL,
    entregador_id INT NOT NULL,
    data_inicio TIMESTAMP NOT NULL,
    data_fim TIMESTAMP NULL,
    origem_latitude DECIMAL(10, 8),
    origem_longitude DECIMAL(11, 8),
    destino_latitude DECIMAL(10, 8),
    destino_longitude DECIMAL(11, 8),
    distancia_km DECIMAL(8, 2),
    duracao_minutos INT AS (TIMESTAMPDIFF(MINUTE, data_inicio, data_fim)) STORED,
    status ENUM('agendada', 'em_andamento', 'concluida', 'cancelada') DEFAULT 'em_andamento',
    valor DECIMAL(10, 2),
    avaliacao_entregador INT CHECK (avaliacao_entregador BETWEEN 1 AND 5),
    observacoes TEXT,
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE RESTRICT,
    FOREIGN KEY (entregador_id) REFERENCES entregadores(id) ON DELETE RESTRICT,
    INDEX idx_moto_viagens (moto_id, data_inicio),
    INDEX idx_entregador_viagens (entregador_id, data_inicio),
    INDEX idx_status_data (status, data_inicio)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: sensores_iot
-- ============================================
CREATE TABLE sensores_iot (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    moto_id INT NOT NULL,
    tipo_sensor ENUM('gps', 'acelerometro', 'giroscopio', 'temperatura', 
                     'bateria', 'velocidade', 'pressao_pneu', 'camera') NOT NULL,
    valor DECIMAL(10, 4),
    unidade VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_sensor ENUM('online', 'offline', 'erro', 'calibracao') DEFAULT 'online',
    metadata JSON,
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE CASCADE,
    INDEX idx_moto_sensor_timestamp (moto_id, tipo_sensor, timestamp),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: deteccoes_visao
-- ============================================
CREATE TABLE deteccoes_visao (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    moto_id INT,
    camera_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    placa_detectada VARCHAR(10),
    confianca DECIMAL(5, 4) CHECK (confianca BETWEEN 0 AND 1),
    coordenadas_imagem JSON,
    imagem_url VARCHAR(500),
    tipo_deteccao ENUM('placa', 'moto', 'capacete', 'movimento', 'anomalia'),
    processado BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE SET NULL,
    INDEX idx_timestamp (timestamp),
    INDEX idx_camera (camera_id, timestamp),
    INDEX idx_processado (processado, timestamp)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: cameras
-- ============================================
CREATE TABLE cameras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    identificador VARCHAR(50) UNIQUE NOT NULL,
    nome VARCHAR(100),
    localizacao VARCHAR(200),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    tipo ENUM('fixa', 'ptz', 'dome', 'bullet', 'ip'),
    resolucao VARCHAR(20),
    fps INT,
    status ENUM('ativa', 'inativa', 'manutencao', 'erro') DEFAULT 'ativa',
    url_stream VARCHAR(500),
    data_instalacao DATE,
    ultima_manutencao DATE,
    campo_visao_graus INT
) ENGINE=InnoDB;

-- ============================================
-- TABELA: usuarios
-- ============================================
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    nome_completo VARCHAR(100),
    role ENUM('admin', 'operador', 'visualizador', 'mecanico') DEFAULT 'operador',
    ativo BOOLEAN DEFAULT TRUE,
    ultimo_acesso TIMESTAMP NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    token_reset VARCHAR(255),
    expiracao_token TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: logs_sistema
-- ============================================
CREATE TABLE logs_sistema (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    acao VARCHAR(100) NOT NULL,
    entidade VARCHAR(50),
    entidade_id INT,
    detalhes JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    INDEX idx_timestamp (timestamp),
    INDEX idx_usuario (usuario_id, timestamp)
) ENGINE=InnoDB;

-- ============================================
-- VIEWS
-- ============================================

-- View: Localização atual das motos
CREATE VIEW v_localizacao_atual AS
SELECT 
    m.id,
    m.placa,
    m.modelo,
    m.status,
    l.latitude,
    l.longitude,
    l.velocidade,
    l.timestamp,
    l.origem_dados
FROM motos m
INNER JOIN (
    SELECT 
        moto_id,
        latitude,
        longitude,
        velocidade,
        timestamp,
        origem_dados,
        ROW_NUMBER() OVER (PARTITION BY moto_id ORDER BY timestamp DESC) as rn
    FROM localizacoes
) l ON m.id = l.moto_id AND l.rn = 1;

-- View: Dashboard resumo
CREATE VIEW v_dashboard_resumo AS
SELECT 
    (SELECT COUNT(*) FROM motos WHERE status = 'disponivel') AS motos_disponiveis,
    (SELECT COUNT(*) FROM motos WHERE status = 'em_uso') AS motos_em_uso,
    (SELECT COUNT(*) FROM motos WHERE status = 'manutencao') AS motos_manutencao,
    (SELECT COUNT(*) FROM alertas WHERE resolvido = FALSE) AS alertas_ativos,
    (SELECT COUNT(*) FROM alertas WHERE resolvido = FALSE AND severidade = 'critica') AS alertas_criticos,
    (SELECT COUNT(*) FROM viagens WHERE status = 'em_andamento') AS viagens_ativas,
    (SELECT COUNT(*) FROM entregadores WHERE status = 'ativo') AS entregadores_ativos;

-- ============================================
-- TRIGGERS
-- ============================================

DELIMITER $$

-- Trigger: Criar alerta de bateria baixa
CREATE TRIGGER trigger_verificar_bateria
AFTER UPDATE ON motos
FOR EACH ROW
BEGIN
    IF NEW.bateria_percentual <= 20 AND OLD.bateria_percentual > 20 THEN
        INSERT INTO alertas (moto_id, tipo, severidade, mensagem, detalhes)
        VALUES (
            NEW.id,
            'bateria_baixa',
            IF(NEW.bateria_percentual <= 10, 'critica', 'media'),
            CONCAT('Bateria da moto ', NEW.placa, ' está em ', NEW.bateria_percentual, '%'),
            JSON_OBJECT('bateria', NEW.bateria_percentual, 'placa', NEW.placa)
        );
    END IF;
END$$

DELIMITER ;

-- ============================================
-- STORED PROCEDURES
-- ============================================

DELIMITER $$

-- Procedure: Calcular distância entre dois pontos
CREATE PROCEDURE sp_calcular_distancia_km(
    IN lat1 DECIMAL(10,8),
    IN lon1 DECIMAL(11,8),
    IN lat2 DECIMAL(10,8),
    IN lon2 DECIMAL(11,8),
    OUT distancia DECIMAL(10,2)
)
BEGIN
    DECLARE R DECIMAL(10,2) DEFAULT 6371;
    DECLARE dLat DECIMAL(10,8);
    DECLARE dLon DECIMAL(11,8);
    DECLARE a DECIMAL(20,10);
    DECLARE c DECIMAL(20,10);
    
    SET dLat = RADIANS(lat2 - lat1);
    SET dLon = RADIANS(lon2 - lon1);
    
    SET a = SIN(dLat/2) * SIN(dLat/2) +
            COS(RADIANS(lat1)) * COS(RADIANS(lat2)) *
            SIN(dLon/2) * SIN(dLon/2);
    
    SET c = 2 * ATAN2(SQRT(a), SQRT(1-a));
    SET distancia = R * c;
END$$

-- Procedure: Obter motos em área específica
CREATE PROCEDURE sp_motos_em_area(IN area_id_param INT)
BEGIN
    SELECT 
        ma.moto_id,
        m.placa,
        TIMESTAMPDIFF(MINUTE, ma.entrada, CURRENT_TIMESTAMP) AS tempo_permanencia_minutos
    FROM motos_areas ma
    INNER JOIN motos m ON ma.moto_id = m.id
    WHERE ma.area_id = area_id_param
    AND ma.saida IS NULL
    ORDER BY ma.entrada DESC;
END$$

DELIMITER ;

-- ============================================
-- DADOS DE EXEMPLO
-- ============================================

-- Inserir áreas do pátio
INSERT INTO areas_patio (nome, tipo, capacidade, descricao) VALUES
('Área A - Estacionamento Principal', 'estacionamento', 50, 'Área principal de estacionamento de motos disponíveis'),
('Área B - Manutenção', 'manutencao', 10, 'Área destinada a motos em manutenção'),
('Área C - Carregamento', 'carga', 20, 'Área para carregamento de baterias'),
('Entrada Principal', 'entrada', 5, 'Ponto de entrada de motos no pátio'),
('Saída Principal', 'saida', 5, 'Ponto de saída de motos do pátio');

-- Inserir câmeras
INSERT INTO cameras (identificador, nome, localizacao, tipo, status, resolucao, fps) VALUES
('CAM001', 'Câmera Entrada', 'Portão Principal', 'fixa', 'ativa', '1920x1080', 30),
('CAM002', 'Câmera Pátio Norte', 'Área de Estacionamento Norte', 'ptz', 'ativa', '1920x1080', 30),
('CAM003', 'Câmera Pátio Sul', 'Área de Estacionamento Sul', 'dome', 'ativa', '2560x1440', 30),
('CAM004', 'Câmera Manutenção', 'Oficina de Manutenção', 'bullet', 'ativa', '1920x1080', 25);CREATE DATABASE IF NOT EXISTS mottu_tracking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mottu_tracking;

-- ============================================
-- TABELA: motos
-- ============================================
CREATE TABLE motos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    placa VARCHAR(10) UNIQUE NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    marca VARCHAR(50) NOT NULL,
    ano INT NOT NULL,
    cor VARCHAR(30),
    numero_chassi VARCHAR(50) UNIQUE,
    status ENUM('disponivel', 'em_uso', 'manutencao', 'inativa') DEFAULT 'disponivel',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    quilometragem DECIMAL(10, 2) DEFAULT 0,
    bateria_percentual INT CHECK (bateria_percentual BETWEEN 0 AND 100),
    observacoes TEXT,
    INDEX idx_status (status),
    INDEX idx_placa (placa)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: localizacoes
-- ============================================
CREATE TABLE localizacoes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    moto_id INT NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    velocidade DECIMAL(5, 2) DEFAULT 0,
    direcao VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    origem_dados ENUM('iot', 'visao_computacional', 'manual', 'gps') DEFAULT 'iot',
    precisao DECIMAL(5, 2),
    altitude DECIMAL(8, 2),
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE CASCADE,
    INDEX idx_moto_timestamp (moto_id, timestamp),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: areas_patio
-- ============================================
CREATE TABLE areas_patio (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    tipo ENUM('estacionamento', 'manutencao', 'carga', 'entrada', 'saida', 'restrita'),
    capacidade INT,
    coordenadas_poligono JSON,
    descricao TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================
-- TABELA: motos_areas
-- ============================================
CREATE TABLE motos_areas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    moto_id INT NOT NULL,
    area_id INT NOT NULL,
    entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    saida TIMESTAMP NULL,
    duracao_minutos INT AS (TIMESTAMPDIFF(MINUTE, entrada, saida)) STORED,
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE CASCADE,
    FOREIGN KEY (area_id) REFERENCES areas_patio(id) ON DELETE CASCADE,
    INDEX idx_moto_periodo (moto_id, entrada, saida)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: alertas
-- ============================================
CREATE TABLE alertas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    moto_id INT,
    tipo ENUM('bateria_baixa', 'manutencao_necessaria', 'velocidade_alta', 
              'area_nao_autorizada', 'inatividade', 'colisao', 
              'roubo_suspeito', 'sensor_offline', 'outro') NOT NULL,
    severidade ENUM('baixa', 'media', 'alta', 'critica') DEFAULT 'media',
    mensagem TEXT NOT NULL,
    detalhes JSON,
    resolvido BOOLEAN DEFAULT FALSE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_resolucao TIMESTAMP NULL,
    resolvido_por VARCHAR(100),
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE SET NULL,
    INDEX idx_moto_alertas (moto_id, data_criacao),
    INDEX idx_nao_resolvidos (resolvido, data_criacao),
    INDEX idx_tipo_severidade (tipo, severidade, resolvido)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: manutencoes
-- ============================================
CREATE TABLE manutencoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    moto_id INT NOT NULL,
    tipo ENUM('preventiva', 'corretiva', 'revisao', 'troca_oleo', 
              'troca_pneu', 'freios', 'eletrica', 'bateria', 'outra') NOT NULL,
    descricao TEXT NOT NULL,
    custo DECIMAL(10, 2),
    data_inicio TIMESTAMP NOT NULL,
    data_conclusao TIMESTAMP NULL,
    status ENUM('agendada', 'em_andamento', 'concluida', 'cancelada') DEFAULT 'agendada',
    mecanico VARCHAR(100),
    observacoes TEXT,
    proxima_manutencao DATE,
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE CASCADE,
    INDEX idx_moto_manutencao (moto_id, data_inicio)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: entregadores
-- ============================================
CREATE TABLE entregadores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    cnh VARCHAR(20) UNIQUE NOT NULL,
    categoria_cnh VARCHAR(5),
    telefone VARCHAR(20),
    email VARCHAR(100) UNIQUE,
    status ENUM('ativo', 'inativo', 'suspenso', 'ferias') DEFAULT 'ativo',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    avaliacao DECIMAL(3, 2) CHECK (avaliacao BETWEEN 0 AND 5),
    total_entregas INT DEFAULT 0,
    INDEX idx_cpf (cpf),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: viagens
-- ============================================
CREATE TABLE viagens (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    moto_id INT NOT NULL,
    entregador_id INT NOT NULL,
    data_inicio TIMESTAMP NOT NULL,
    data_fim TIMESTAMP NULL,
    origem_latitude DECIMAL(10, 8),
    origem_longitude DECIMAL(11, 8),
    destino_latitude DECIMAL(10, 8),
    destino_longitude DECIMAL(11, 8),
    distancia_km DECIMAL(8, 2),
    duracao_minutos INT AS (TIMESTAMPDIFF(MINUTE, data_inicio, data_fim)) STORED,
    status ENUM('agendada', 'em_andamento', 'concluida', 'cancelada') DEFAULT 'em_andamento',
    valor DECIMAL(10, 2),
    avaliacao_entregador INT CHECK (avaliacao_entregador BETWEEN 1 AND 5),
    observacoes TEXT,
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE RESTRICT,
    FOREIGN KEY (entregador_id) REFERENCES entregadores(id) ON DELETE RESTRICT,
    INDEX idx_moto_viagens (moto_id, data_inicio),
    INDEX idx_entregador_viagens (entregador_id, data_inicio),
    INDEX idx_status_data (status, data_inicio)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: sensores_iot
-- ============================================
CREATE TABLE sensores_iot (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    moto_id INT NOT NULL,
    tipo_sensor ENUM('gps', 'acelerometro', 'giroscopio', 'temperatura', 
                     'bateria', 'velocidade', 'pressao_pneu', 'camera') NOT NULL,
    valor DECIMAL(10, 4),
    unidade VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_sensor ENUM('online', 'offline', 'erro', 'calibracao') DEFAULT 'online',
    metadata JSON,
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE CASCADE,
    INDEX idx_moto_sensor_timestamp (moto_id, tipo_sensor, timestamp),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: deteccoes_visao
-- ============================================
CREATE TABLE deteccoes_visao (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    moto_id INT,
    camera_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    placa_detectada VARCHAR(10),
    confianca DECIMAL(5, 4) CHECK (confianca BETWEEN 0 AND 1),
    coordenadas_imagem JSON,
    imagem_url VARCHAR(500),
    tipo_deteccao ENUM('placa', 'moto', 'capacete', 'movimento', 'anomalia'),
    processado BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE SET NULL,
    INDEX idx_timestamp (timestamp),
    INDEX idx_camera (camera_id, timestamp),
    INDEX idx_processado (processado, timestamp)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: cameras
-- ============================================
CREATE TABLE cameras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    identificador VARCHAR(50) UNIQUE NOT NULL,
    nome VARCHAR(100),
    localizacao VARCHAR(200),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    tipo ENUM('fixa', 'ptz', 'dome', 'bullet', 'ip'),
    resolucao VARCHAR(20),
    fps INT,
    status ENUM('ativa', 'inativa', 'manutencao', 'erro') DEFAULT 'ativa',
    url_stream VARCHAR(500),
    data_instalacao DATE,
    ultima_manutencao DATE,
    campo_visao_graus INT
) ENGINE=InnoDB;

-- ============================================
-- TABELA: usuarios
-- ============================================
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    nome_completo VARCHAR(100),
    role ENUM('admin', 'operador', 'visualizador', 'mecanico') DEFAULT 'operador',
    ativo BOOLEAN DEFAULT TRUE,
    ultimo_acesso TIMESTAMP NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    token_reset VARCHAR(255),
    expiracao_token TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB;

-- ============================================
-- TABELA: logs_sistema
-- ============================================
CREATE TABLE logs_sistema (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    acao VARCHAR(100) NOT NULL,
    entidade VARCHAR(50),
    entidade_id INT,
    detalhes JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    INDEX idx_timestamp (timestamp),
    INDEX idx_usuario (usuario_id, timestamp)
) ENGINE=InnoDB;

-- ============================================
-- VIEWS
-- ============================================

-- View: Localização atual das motos
CREATE VIEW v_localizacao_atual AS
SELECT 
    m.id,
    m.placa,
    m.modelo,
    m.status,
    l.latitude,
    l.longitude,
    l.velocidade,
    l.timestamp,
    l.origem_dados
FROM motos m
INNER JOIN (
    SELECT 
        moto_id,
        latitude,
        longitude,
        velocidade,
        timestamp,
        origem_dados,
        ROW_NUMBER() OVER (PARTITION BY moto_id ORDER BY timestamp DESC) as rn
    FROM localizacoes
) l ON m.id = l.moto_id AND l.rn = 1;

-- View: Dashboard resumo
CREATE VIEW v_dashboard_resumo AS
SELECT 
    (SELECT COUNT(*) FROM motos WHERE status = 'disponivel') AS motos_disponiveis,
    (SELECT COUNT(*) FROM motos WHERE status = 'em_uso') AS motos_em_uso,
    (SELECT COUNT(*) FROM motos WHERE status = 'manutencao') AS motos_manutencao,
    (SELECT COUNT(*) FROM alertas WHERE resolvido = FALSE) AS alertas_ativos,
    (SELECT COUNT(*) FROM alertas WHERE resolvido = FALSE AND severidade = 'critica') AS alertas_criticos,
    (SELECT COUNT(*) FROM viagens WHERE status = 'em_andamento') AS viagens_ativas,
    (SELECT COUNT(*) FROM entregadores WHERE status = 'ativo') AS entregadores_ativos;

-- ============================================
-- TRIGGERS
-- ============================================

DELIMITER $$

-- Trigger: Criar alerta de bateria baixa
CREATE TRIGGER trigger_verificar_bateria
AFTER UPDATE ON motos
FOR EACH ROW
BEGIN
    IF NEW.bateria_percentual <= 20 AND OLD.bateria_percentual > 20 THEN
        INSERT INTO alertas (moto_id, tipo, severidade, mensagem, detalhes)
        VALUES (
            NEW.id,
            'bateria_baixa',
            IF(NEW.bateria_percentual <= 10, 'critica', 'media'),
            CONCAT('Bateria da moto ', NEW.placa, ' está em ', NEW.bateria_percentual, '%'),
            JSON_OBJECT('bateria', NEW.bateria_percentual, 'placa', NEW.placa)
        );
    END IF;
END$$

DELIMITER ;

-- ============================================
-- STORED PROCEDURES
-- ============================================

DELIMITER $$

-- Procedure: Calcular distância entre dois pontos
CREATE PROCEDURE sp_calcular_distancia_km(
    IN lat1 DECIMAL(10,8),
    IN lon1 DECIMAL(11,8),
    IN lat2 DECIMAL(10,8),
    IN lon2 DECIMAL(11,8),
    OUT distancia DECIMAL(10,2)
)
BEGIN
    DECLARE R DECIMAL(10,2) DEFAULT 6371;
    DECLARE dLat DECIMAL(10,8);
    DECLARE dLon DECIMAL(11,8);
    DECLARE a DECIMAL(20,10);
    DECLARE c DECIMAL(20,10);
    
    SET dLat = RADIANS(lat2 - lat1);
    SET dLon = RADIANS(lon2 - lon1);
    
    SET a = SIN(dLat/2) * SIN(dLat/2) +
            COS(RADIANS(lat1)) * COS(RADIANS(lat2)) *
            SIN(dLon/2) * SIN(dLon/2);
    
    SET c = 2 * ATAN2(SQRT(a), SQRT(1-a));
    SET distancia = R * c;
END$$

-- Procedure: Obter motos em área específica
CREATE PROCEDURE sp_motos_em_area(IN area_id_param INT)
BEGIN
    SELECT 
        ma.moto_id,
        m.placa,
        TIMESTAMPDIFF(MINUTE, ma.entrada, CURRENT_TIMESTAMP) AS tempo_permanencia_minutos
    FROM motos_areas ma
    INNER JOIN motos m ON ma.moto_id = m.id
    WHERE ma.area_id = area_id_param
    AND ma.saida IS NULL
    ORDER BY ma.entrada DESC;
END$$

DELIMITER ;

-- ============================================
-- DADOS DE EXEMPLO
-- ============================================

-- Inserir áreas do pátio
INSERT INTO areas_patio (nome, tipo, capacidade, descricao) VALUES
('Área A - Estacionamento Principal', 'estacionamento', 50, 'Área principal de estacionamento de motos disponíveis'),
('Área B - Manutenção', 'manutencao', 10, 'Área destinada a motos em manutenção'),
('Área C - Carregamento', 'carga', 20, 'Área para carregamento de baterias'),
('Entrada Principal', 'entrada', 5, 'Ponto de entrada de motos no pátio'),
('Saída Principal', 'saida', 5, 'Ponto de saída de motos do pátio');

-- Inserir câmeras
INSERT INTO cameras (identificador, nome, localizacao, tipo, status, resolucao, fps) VALUES
('CAM001', 'Câmera Entrada', 'Portão Principal', 'fixa', 'ativa', '1920x1080', 30),
('CAM002', 'Câmera Pátio Norte', 'Área de Estacionamento Norte', 'ptz', 'ativa', '1920x1080', 30),
('CAM003', 'Câmera Pátio Sul', 'Área de Estacionamento Sul', 'dome', 'ativa', '2560x1440', 30),
('CAM004', 'Câmera Manutenção', 'Oficina de Manutenção', 'bullet', 'ativa', '1920x1080', 25);