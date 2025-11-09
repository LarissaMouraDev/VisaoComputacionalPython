-- ============================================
-- BANCO DE DADOS MOTTU - RASTREAMENTO DE MOTOS
-- Sistema de Visão Computacional + IoT
-- PostgreSQL
-- ============================================

-- Criação do banco de dados
CREATE DATABASE mottu_tracking;

\c mottu_tracking;

-- ============================================
-- TABELA: motos
-- Armazena informações cadastrais das motos
-- ============================================
CREATE TABLE motos (
    id SERIAL PRIMARY KEY,
    placa VARCHAR(10) UNIQUE NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    marca VARCHAR(50) NOT NULL,
    ano INTEGER NOT NULL,
    cor VARCHAR(30),
    numero_chassi VARCHAR(50) UNIQUE,
    status VARCHAR(20) DEFAULT 'disponivel' CHECK (status IN ('disponivel', 'em_uso', 'manutencao', 'inativa')),
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quilometragem DECIMAL(10, 2) DEFAULT 0,
    bateria_percentual INTEGER CHECK (bateria_percentual BETWEEN 0 AND 100),
    observacoes TEXT
);

-- ============================================
-- TABELA: localizacoes
-- Registra a localização das motos em tempo real
-- ============================================
CREATE TABLE localizacoes (
    id SERIAL PRIMARY KEY,
    moto_id INTEGER NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    velocidade DECIMAL(5, 2) DEFAULT 0,
    direcao VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    origem_dados VARCHAR(20) DEFAULT 'iot' CHECK (origem_dados IN ('iot', 'visao_computacional', 'manual', 'gps')),
    precisao DECIMAL(5, 2),
    altitude DECIMAL(8, 2),
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE CASCADE,
    INDEX idx_moto_timestamp (moto_id, timestamp),
    INDEX idx_timestamp (timestamp)
);

-- ============================================
-- TABELA: areas_patio
-- Define áreas/zonas do pátio da Mottu
-- ============================================
CREATE TABLE areas_patio (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    tipo VARCHAR(30) CHECK (tipo IN ('estacionamento', 'manutencao', 'carga', 'entrada', 'saida', 'restrita')),
    capacidade INTEGER,
    coordenadas_poligono JSON, -- Armazena polígono da área [[lat, lng], [lat, lng], ...]
    descricao TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABELA: motos_areas
-- Relaciona motos com áreas do pátio
-- ============================================
CREATE TABLE motos_areas (
    id SERIAL PRIMARY KEY,
    moto_id INTEGER NOT NULL,
    area_id INTEGER NOT NULL,
    entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    saida TIMESTAMP,
    duracao_minutos INTEGER GENERATED ALWAYS AS (
        CASE 
            WHEN saida IS NOT NULL THEN EXTRACT(EPOCH FROM (saida - entrada))/60
            ELSE NULL
        END
    ) STORED,
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE CASCADE,
    FOREIGN KEY (area_id) REFERENCES areas_patio(id) ON DELETE CASCADE,
    INDEX idx_moto_periodo (moto_id, entrada, saida)
);

-- ============================================
-- TABELA: alertas
-- Registra alertas e notificações do sistema
-- ============================================
CREATE TABLE alertas (
    id SERIAL PRIMARY KEY,
    moto_id INTEGER,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN (
        'bateria_baixa', 'manutencao_necessaria', 'velocidade_alta', 
        'area_nao_autorizada', 'inatividade', 'colisao', 
        'roubo_suspeito', 'sensor_offline', 'outro'
    )),
    severidade VARCHAR(20) DEFAULT 'media' CHECK (severidade IN ('baixa', 'media', 'alta', 'critica')),
    mensagem TEXT NOT NULL,
    detalhes JSON,
    resolvido BOOLEAN DEFAULT FALSE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_resolucao TIMESTAMP,
    resolvido_por VARCHAR(100),
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE SET NULL,
    INDEX idx_moto_alertas (moto_id, data_criacao),
    INDEX idx_nao_resolvidos (resolvido, data_criacao)
);

-- ============================================
-- TABELA: manutencoes
-- Histórico de manutenções das motos
-- ============================================
CREATE TABLE manutencoes (
    id SERIAL PRIMARY KEY,
    moto_id INTEGER NOT NULL,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN (
        'preventiva', 'corretiva', 'revisao', 'troca_oleo', 
        'troca_pneu', 'freios', 'eletrica', 'bateria', 'outra'
    )),
    descricao TEXT NOT NULL,
    custo DECIMAL(10, 2),
    data_inicio TIMESTAMP NOT NULL,
    data_conclusao TIMESTAMP,
    status VARCHAR(20) DEFAULT 'agendada' CHECK (status IN ('agendada', 'em_andamento', 'concluida', 'cancelada')),
    mecanico VARCHAR(100),
    observacoes TEXT,
    proxima_manutencao DATE,
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE CASCADE,
    INDEX idx_moto_manutencao (moto_id, data_inicio)
);

-- ============================================
-- TABELA: entregadores
-- Cadastro de entregadores da Mottu
-- ============================================
CREATE TABLE entregadores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    cnh VARCHAR(20) UNIQUE NOT NULL,
    categoria_cnh VARCHAR(5),
    telefone VARCHAR(20),
    email VARCHAR(100) UNIQUE,
    status VARCHAR(20) DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo', 'suspenso', 'ferias')),
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    avaliacao DECIMAL(3, 2) CHECK (avaliacao BETWEEN 0 AND 5),
    total_entregas INTEGER DEFAULT 0
);

-- ============================================
-- TABELA: viagens
-- Registro de viagens/entregas realizadas
-- ============================================
CREATE TABLE viagens (
    id SERIAL PRIMARY KEY,
    moto_id INTEGER NOT NULL,
    entregador_id INTEGER NOT NULL,
    data_inicio TIMESTAMP NOT NULL,
    data_fim TIMESTAMP,
    origem_latitude DECIMAL(10, 8),
    origem_longitude DECIMAL(11, 8),
    destino_latitude DECIMAL(10, 8),
    destino_longitude DECIMAL(11, 8),
    distancia_km DECIMAL(8, 2),
    duracao_minutos INTEGER GENERATED ALWAYS AS (
        CASE 
            WHEN data_fim IS NOT NULL THEN EXTRACT(EPOCH FROM (data_fim - data_inicio))/60
            ELSE NULL
        END
    ) STORED,
    status VARCHAR(20) DEFAULT 'em_andamento' CHECK (status IN ('agendada', 'em_andamento', 'concluida', 'cancelada')),
    valor DECIMAL(10, 2),
    avaliacao_entregador INTEGER CHECK (avaliacao_entregador BETWEEN 1 AND 5),
    observacoes TEXT,
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE RESTRICT,
    FOREIGN KEY (entregador_id) REFERENCES entregadores(id) ON DELETE RESTRICT,
    INDEX idx_moto_viagens (moto_id, data_inicio),
    INDEX idx_entregador_viagens (entregador_id, data_inicio)
);

-- ============================================
-- TABELA: sensores_iot
-- Dados dos sensores IoT instalados nas motos
-- ============================================
CREATE TABLE sensores_iot (
    id SERIAL PRIMARY KEY,
    moto_id INTEGER NOT NULL,
    tipo_sensor VARCHAR(50) NOT NULL CHECK (tipo_sensor IN (
        'gps', 'acelerometro', 'giroscopio', 'temperatura', 
        'bateria', 'velocidade', 'pressao_pneu', 'camera'
    )),
    valor DECIMAL(10, 4),
    unidade VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_sensor VARCHAR(20) DEFAULT 'online' CHECK (status_sensor IN ('online', 'offline', 'erro', 'calibracao')),
    metadata JSON,
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE CASCADE,
    INDEX idx_moto_sensor_timestamp (moto_id, tipo_sensor, timestamp)
);

-- ============================================
-- TABELA: deteccoes_visao
-- Registros de detecção por visão computacional
-- ============================================
CREATE TABLE deteccoes_visao (
    id SERIAL PRIMARY KEY,
    moto_id INTEGER,
    camera_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    placa_detectada VARCHAR(10),
    confianca DECIMAL(5, 4) CHECK (confianca BETWEEN 0 AND 1),
    coordenadas_imagem JSON, -- Bounding box [x, y, width, height]
    imagem_url VARCHAR(500),
    tipo_deteccao VARCHAR(30) CHECK (tipo_deteccao IN ('placa', 'moto', 'capacete', 'movimento', 'anomalia')),
    processado BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (moto_id) REFERENCES motos(id) ON DELETE SET NULL,
    INDEX idx_timestamp (timestamp),
    INDEX idx_camera (camera_id, timestamp)
);

-- ============================================
-- TABELA: cameras
-- Câmeras do sistema de visão computacional
-- ============================================
CREATE TABLE cameras (
    id SERIAL PRIMARY KEY,
    identificador VARCHAR(50) UNIQUE NOT NULL,
    nome VARCHAR(100),
    localizacao VARCHAR(200),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    tipo VARCHAR(30) CHECK (tipo IN ('fixa', 'ptz', 'dome', 'bullet', 'ip')),
    resolucao VARCHAR(20),
    fps INTEGER,
    status VARCHAR(20) DEFAULT 'ativa' CHECK (status IN ('ativa', 'inativa', 'manutencao', 'erro')),
    url_stream VARCHAR(500),
    data_instalacao DATE,
    ultima_manutencao DATE,
    campo_visao_graus INTEGER
);

-- ============================================
-- TABELA: usuarios
-- Usuários do sistema (admin, operadores, etc)
-- ============================================
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    nome_completo VARCHAR(100),
    role VARCHAR(20) DEFAULT 'operador' CHECK (role IN ('admin', 'operador', 'visualizador', 'mecanico')),
    ativo BOOLEAN DEFAULT TRUE,
    ultimo_acesso TIMESTAMP,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    token_reset VARCHAR(255),
    expiracao_token TIMESTAMP
);

-- ============================================
-- TABELA: logs_sistema
-- Log de eventos do sistema
-- ============================================
CREATE TABLE logs_sistema (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER,
    acao VARCHAR(100) NOT NULL,
    entidade VARCHAR(50),
    entidade_id INTEGER,
    detalhes JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    INDEX idx_timestamp (timestamp),
    INDEX idx_usuario (usuario_id, timestamp)
);

-- ============================================
-- VIEWS ÚTEIS
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
INNER JOIN LATERAL (
    SELECT latitude, longitude, velocidade, timestamp, origem_dados
    FROM localizacoes
    WHERE moto_id = m.id
    ORDER BY timestamp DESC
    LIMIT 1
) l ON true;

-- View: Motos com alertas ativos
CREATE VIEW v_motos_com_alertas AS
SELECT 
    m.id AS moto_id,
    m.placa,
    m.modelo,
    COUNT(a.id) AS total_alertas,
    COUNT(CASE WHEN a.severidade = 'critica' THEN 1 END) AS alertas_criticos,
    MAX(a.data_criacao) AS ultimo_alerta
FROM motos m
INNER JOIN alertas a ON m.id = a.moto_id
WHERE a.resolvido = FALSE
GROUP BY m.id, m.placa, m.modelo;

-- View: Estatísticas de viagens por moto
CREATE VIEW v_estatisticas_motos AS
SELECT 
    m.id,
    m.placa,
    m.modelo,
    m.quilometragem,
    COUNT(v.id) AS total_viagens,
    COALESCE(SUM(v.distancia_km), 0) AS distancia_total_viagens,
    COALESCE(AVG(v.duracao_minutos), 0) AS tempo_medio_viagem,
    COUNT(CASE WHEN v.status = 'concluida' THEN 1 END) AS viagens_concluidas
FROM motos m
LEFT JOIN viagens v ON m.id = v.moto_id
GROUP BY m.id, m.placa, m.modelo, m.quilometragem;

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

-- Trigger: Atualizar última atualização da moto
CREATE OR REPLACE FUNCTION atualizar_timestamp_moto()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE motos SET ultima_atualizacao = CURRENT_TIMESTAMP WHERE id = NEW.moto_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_atualizar_moto_localizacao
AFTER INSERT ON localizacoes
FOR EACH ROW
EXECUTE FUNCTION atualizar_timestamp_moto();

-- Trigger: Criar alerta de bateria baixa
CREATE OR REPLACE FUNCTION verificar_bateria_baixa()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.bateria_percentual <= 20 AND OLD.bateria_percentual > 20 THEN
        INSERT INTO alertas (moto_id, tipo, severidade, mensagem, detalhes)
        VALUES (
            NEW.id,
            'bateria_baixa',
            CASE WHEN NEW.bateria_percentual <= 10 THEN 'critica' ELSE 'media' END,
            'Bateria da moto ' || NEW.placa || ' está em ' || NEW.bateria_percentual || '%',
            json_build_object('bateria', NEW.bateria_percentual, 'placa', NEW.placa)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_verificar_bateria
AFTER UPDATE OF bateria_percentual ON motos
FOR EACH ROW
EXECUTE FUNCTION verificar_bateria_baixa();

-- ============================================
-- FUNÇÕES ÚTEIS
-- ============================================

-- Função: Calcular distância entre dois pontos (Haversine)
CREATE OR REPLACE FUNCTION calcular_distancia_km(
    lat1 DECIMAL, lon1 DECIMAL,
    lat2 DECIMAL, lon2 DECIMAL
)
RETURNS DECIMAL AS $$
DECLARE
    R DECIMAL := 6371; -- Raio da Terra em km
    dLat DECIMAL;
    dLon DECIMAL;
    a DECIMAL;
    c DECIMAL;
BEGIN
    dLat := RADIANS(lat2 - lat1);
    dLon := RADIANS(lon2 - lon1);
    
    a := SIN(dLat/2) * SIN(dLat/2) +
         COS(RADIANS(lat1)) * COS(RADIANS(lat2)) *
         SIN(dLon/2) * SIN(dLon/2);
    
    c := 2 * ATAN2(SQRT(a), SQRT(1-a));
    
    RETURN R * c;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Função: Obter motos em área específica
CREATE OR REPLACE FUNCTION motos_em_area(area_id_param INTEGER)
RETURNS TABLE (
    moto_id INTEGER,
    placa VARCHAR,
    tempo_permanencia_minutos INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ma.moto_id,
        m.placa,
        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - ma.entrada))::INTEGER / 60 AS tempo_permanencia_minutos
    FROM motos_areas ma
    INNER JOIN motos m ON ma.moto_id = m.id
    WHERE ma.area_id = area_id_param
    AND ma.saida IS NULL
    ORDER BY ma.entrada DESC;
END;
$$ LANGUAGE plpgsql;


-- ÍNDICES ADICIONAIS PARA PERFORMANCE
-- ============================================

CREATE INDEX idx_motos_status ON motos(status);
CREATE INDEX idx_alertas_tipo_severidade ON alertas(tipo, severidade, resolvido);
CREATE INDEX idx_viagens_status_data ON viagens(status, data_inicio);
CREATE INDEX idx_sensores_timestamp ON sensores_iot(timestamp DESC);
CREATE INDEX idx_deteccoes_processado ON deteccoes_visao(processado, timestamp);


-- DADOS DE EXEMPLO (OPCIONAL)
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

-- Inserir usuário admin (senha: admin123 - TROCAR EM PRODUÇÃO!)
INSERT INTO usuarios (username, email, senha_hash, nome_completo, role) VALUES
('admin', 'admin@mottu.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeOLNa9fZvxi', 'Administrador Sistema', 'admin'),
('operador1', 'operador@mottu.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeOLNa9fZvxi', 'Operador Principal', 'operador');


-- GRANTS E PERMISSÕES


COMMENT ON DATABASE mottu_tracking IS 'Banco de dados do sistema de rastreamento de motos Mottu - Visão Computacional + IoT';
COMMENT ON TABLE motos IS 'Cadastro principal de motos da frota Mottu';
COMMENT ON TABLE localizacoes IS 'Histórico de localizações GPS/Visão Computacional das motos';
COMMENT ON TABLE alertas IS 'Sistema de alertas e notificações em tempo real';
COMMENT ON TABLE viagens IS 'Registro de viagens e entregas realizadas';
COMMENT ON TABLE sensores_iot IS 'Dados coletados pelos sensores IoT instalados nas motos';
COMMENT ON TABLE deteccoes_visao IS 'Detecções realizadas pelo sistema de visão computacional';

