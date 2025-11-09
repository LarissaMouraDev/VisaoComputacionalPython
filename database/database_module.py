"""
Database Module - Mottu Tracking System
PostgreSQL Connection and Operations
"""

import psycopg2
from psycopg2 import pool, extras
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from contextlib import contextmanager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Configurações do banco de dados"""
    HOST = "localhost"
    PORT = 5432
    DATABASE = "mottu_tracking"
    USER = "postgres"
    PASSWORD = "sua_senha_aqui"
    MIN_CONNECTIONS = 1
    MAX_CONNECTIONS = 20


class Database:
    """Classe principal para gerenciamento do banco de dados"""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.connection_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Inicializa o pool de conexões"""
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                self.config.MIN_CONNECTIONS,
                self.config.MAX_CONNECTIONS,
                host=self.config.HOST,
                port=self.config.PORT,
                database=self.config.DATABASE,
                user=self.config.USER,
                password=self.config.PASSWORD
            )
            logger.info("Pool de conexões inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar pool de conexões: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager para obter conexão do pool"""
        conn = self.connection_pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro na transação: {e}")
            raise
        finally:
            self.connection_pool.putconn(conn)
    
    def close_all_connections(self):
        """Fecha todas as conexões do pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Todas as conexões foram fechadas")


class MotoRepository:
    """Repositório para operações com a tabela motos"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def criar_moto(self, placa: str, modelo: str, marca: str, ano: int, **kwargs) -> int:
        """Cria uma nova moto no sistema"""
        query = """
            INSERT INTO motos (placa, modelo, marca, ano, cor, numero_chassi, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    placa, modelo, marca, ano,
                    kwargs.get('cor'),
                    kwargs.get('numero_chassi'),
                    kwargs.get('status', 'disponivel')
                ))
                moto_id = cur.fetchone()[0]
                logger.info(f"Moto criada com ID: {moto_id}")
                return moto_id
    
    def obter_moto(self, moto_id: int) -> Optional[Dict]:
        """Obtém informações de uma moto"""
        query = "SELECT * FROM motos WHERE id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(query, (moto_id,))
                return cur.fetchone()
    
    def listar_motos(self, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Lista motos com filtro opcional de status"""
        if status:
            query = "SELECT * FROM motos WHERE status = %s LIMIT %s"
            params = (status, limit)
        else:
            query = "SELECT * FROM motos LIMIT %s"
            params = (limit,)
        
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchall()
    
    def atualizar_status(self, moto_id: int, novo_status: str) -> bool:
        """Atualiza o status de uma moto"""
        query = "UPDATE motos SET status = %s WHERE id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (novo_status, moto_id))
                return cur.rowcount > 0
    
    def atualizar_bateria(self, moto_id: int, percentual: int) -> bool:
        """Atualiza o nível de bateria (trigger cria alerta automaticamente)"""
        query = "UPDATE motos SET bateria_percentual = %s WHERE id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (percentual, moto_id))
                return cur.rowcount > 0


class LocalizacaoRepository:
    """Repositório para operações de localização"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def registrar_localizacao(self, moto_id: int, latitude: float, longitude: float, 
                             velocidade: float = 0, origem: str = 'iot', **kwargs) -> int:
        """Registra nova localização da moto"""
        query = """
            INSERT INTO localizacoes 
            (moto_id, latitude, longitude, velocidade, origem_dados, direcao, precisao, altitude)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    moto_id, latitude, longitude, velocidade, origem,
                    kwargs.get('direcao'),
                    kwargs.get('precisao'),
                    kwargs.get('altitude')
                ))
                return cur.fetchone()[0]
    
    def obter_localizacao_atual(self, moto_id: int) -> Optional[Dict]:
        """Obtém a localização mais recente de uma moto"""
        query = """
            SELECT * FROM localizacoes 
            WHERE moto_id = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(query, (moto_id,))
                return cur.fetchone()
    
    def obter_historico(self, moto_id: int, horas: int = 24) -> List[Dict]:
        """Obtém histórico de localizações"""
        query = """
            SELECT * FROM localizacoes 
            WHERE moto_id = %s 
            AND timestamp >= NOW() - INTERVAL '%s hours'
            ORDER BY timestamp DESC
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(query, (moto_id, horas))
                return cur.fetchall()
    
    def obter_todas_localizacoes_atuais(self) -> List[Dict]:
        """Obtém localização atual de todas as motos (usando view)"""
        query = "SELECT * FROM v_localizacao_atual"
        
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchall()


class AlertaRepository:
    """Repositório para operações com alertas"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def criar_alerta(self, moto_id: Optional[int], tipo: str, mensagem: str, 
                     severidade: str = 'media', detalhes: Dict = None) -> int:
        """Cria um novo alerta"""
        query = """
            INSERT INTO alertas (moto_id, tipo, severidade, mensagem, detalhes)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    moto_id, tipo, severidade, mensagem,
                    json.dumps(detalhes) if detalhes else None
                ))
                return cur.fetchone()[0]
    
    def listar_alertas_ativos(self, severidade: Optional[str] = None) -> List[Dict]:
        """Lista alertas não resolvidos"""
        if severidade:
            query = """
                SELECT * FROM alertas 
                WHERE resolvido = FALSE AND severidade = %s
                ORDER BY data_criacao DESC
            """
            params = (severidade,)
        else:
            query = """
                SELECT * FROM alertas 
                WHERE resolvido = FALSE
                ORDER BY data_criacao DESC
            """
            params = ()
        
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchall()
    
    def resolver_alerta(self, alerta_id: int, resolvido_por: str) -> bool:
        """Marca um alerta como resolvido"""
        query = """
            UPDATE alertas 
            SET resolvido = TRUE, data_resolucao = NOW(), resolvido_por = %s
            WHERE id = %s
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (resolvido_por, alerta_id))
                return cur.rowcount > 0


class ViagemRepository:
    """Repositório para operações com viagens"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def iniciar_viagem(self, moto_id: int, entregador_id: int, 
                      origem_lat: float, origem_lon: float) -> int:
        """Inicia uma nova viagem"""
        query = """
            INSERT INTO viagens 
            (moto_id, entregador_id, data_inicio, origem_latitude, origem_longitude, status)
            VALUES (%s, %s, NOW(), %s, %s, 'em_andamento')
            RETURNING id
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (moto_id, entregador_id, origem_lat, origem_lon))
                return cur.fetchone()[0]
    
    def finalizar_viagem(self, viagem_id: int, destino_lat: float, 
                        destino_lon: float, distancia_km: float, valor: float) -> bool:
        """Finaliza uma viagem"""
        query = """
            UPDATE viagens 
            SET data_fim = NOW(), destino_latitude = %s, destino_longitude = %s,
                distancia_km = %s, valor = %s, status = 'concluida'
            WHERE id = %s
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (destino_lat, destino_lon, distancia_km, valor, viagem_id))
                return cur.rowcount > 0
    
    def listar_viagens_ativas(self) -> List[Dict]:
        """Lista viagens em andamento"""
        query = """
            SELECT v.*, m.placa, e.nome as entregador_nome
            FROM viagens v
            JOIN motos m ON v.moto_id = m.id
            JOIN entregadores e ON v.entregador_id = e.id
            WHERE v.status = 'em_andamento'
            ORDER BY v.data_inicio DESC
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchall()


class SensorRepository:
    """Repositório para dados de sensores IoT"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def registrar_leitura(self, moto_id: int, tipo_sensor: str, 
                         valor: float, unidade: str = None, metadata: Dict = None) -> int:
        """Registra leitura de sensor"""
        query = """
            INSERT INTO sensores_iot 
            (moto_id, tipo_sensor, valor, unidade, metadata, status_sensor)
            VALUES (%s, %s, %s, %s, %s, 'online')
            RETURNING id
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    moto_id, tipo_sensor, valor, unidade,
                    json.dumps(metadata) if metadata else None
                ))
                return cur.fetchone()[0]
    
    def obter_ultimas_leituras(self, moto_id: int, tipo_sensor: str, 
                              limite: int = 10) -> List[Dict]:
        """Obtém últimas leituras de um sensor específico"""
        query = """
            SELECT * FROM sensores_iot
            WHERE moto_id = %s AND tipo_sensor = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(query, (moto_id, tipo_sensor, limite))
                return cur.fetchall()


class DashboardRepository:
    """Repositório para dados do dashboard"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def obter_resumo(self) -> Dict:
        """Obtém resumo do dashboard (usando view)"""
        query = "SELECT * FROM v_dashboard_resumo"
        
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchone()
    
    def obter_estatisticas_motos(self) -> List[Dict]:
        """Obtém estatísticas de uso das motos"""
        query = "SELECT * FROM v_estatisticas_motos ORDER BY total_viagens DESC"
        
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchall()
    
    def obter_motos_com_alertas(self) -> List[Dict]:
        """Obtém motos com alertas ativos"""
        query = "SELECT * FROM v_motos_com_alertas ORDER BY alertas_criticos DESC, total_alertas DESC"
        
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchall()



# EXEMPLO DE USO
# ============================================

if __name__ == "__main__":
    # Configurar banco de dados
    config = DatabaseConfig()
    config.HOST = "localhost"
    config.DATABASE = "mottu_tracking"
    config.USER = "postgres"
    config.PASSWORD = "sua_senha"
    
    # Inicializar database
    db = Database(config)
    
    try:
        # Exemplo 1: Criar nova moto
        moto_repo = MotoRepository(db)
        moto_id = moto_repo.criar_moto(
            placa="ABC1D23",
            modelo="Honda CG 160",
            marca="Honda",
            ano=2023,
            cor="Vermelha"
        )
        print(f"Moto criada com ID: {moto_id}")
        
        # Exemplo 2: Registrar localização
        loc_repo = LocalizacaoRepository(db)
        loc_id = loc_repo.registrar_localizacao(
            moto_id=moto_id,
            latitude=-23.5505,
            longitude=-46.6333,
            velocidade=45.5,
            origem='gps'
        )
        print(f"Localização registrada com ID: {loc_id}")
        
        # Exemplo 3: Criar alerta
        alerta_repo = AlertaRepository(db)
        alerta_id = alerta_repo.criar_alerta(
            moto_id=moto_id,
            tipo='bateria_baixa',
            mensagem='Bateria baixa detectada',
            severidade='media',
            detalhes={'percentual': 15}
        )
        print(f"Alerta criado com ID: {alerta_id}")
        
        # Exemplo 4: Obter resumo do dashboard
        dashboard_repo = DashboardRepository(db)
        resumo = dashboard_repo.obter_resumo()
        print(f"Resumo do dashboard: {resumo}")
        
        # Exemplo 5: Listar alertas ativos
        alertas_ativos = alerta_repo.listar_alertas_ativos()
        print(f"Total de alertas ativos: {len(alertas_ativos)}")
        
    finally:
        # Fechar conexões
        db.close_all_connections()
        print("Conexões fechadas")