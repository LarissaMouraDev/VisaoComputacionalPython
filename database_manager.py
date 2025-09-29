import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
import os
from contextlib import contextmanager
import logging
import shutil

class DatabaseManager:
    """
    Gerenciador de banco de dados para o sistema IoT de detecção de motocicletas
    Implementa persistência e estruturação dos dados conforme requisitos
    """
    
    def __init__(self, db_path="iot_motorcycle_system.db"):
        self.db_path = db_path
        self.setup_logging()
        self.initialize_database()
    
    def setup_logging(self):
        """Configura logging para o sistema"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('database.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexões de banco de dados"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Erro na transação do banco: {e}")
            raise
        finally:
            conn.close()
    
    def initialize_database(self):
        """Inicializa o banco de dados com todas as tabelas necessárias"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de dados dos sensores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_id TEXT NOT NULL,
                    sensor_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    location_zone TEXT,
                    latitude REAL,
                    longitude REAL,
                    battery_level INTEGER,
                    status TEXT DEFAULT 'online',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de detecções de motocicletas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS motorcycle_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    detection_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    confidence_score REAL NOT NULL,
                    bbox_x INTEGER NOT NULL,
                    bbox_y INTEGER NOT NULL,
                    bbox_width INTEGER NOT NULL,
                    bbox_height INTEGER NOT NULL,
                    object_class TEXT NOT NULL,
                    image_path TEXT,
                    video_frame INTEGER,
                    processing_time_ms REAL,
                    algorithm_used TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de eventos do sistema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    event_description TEXT,
                    severity_level TEXT DEFAULT 'INFO',
                    component TEXT,
                    additional_data TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resolved_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de configurações do sistema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT UNIQUE NOT NULL,
                    config_value TEXT NOT NULL,
                    config_type TEXT DEFAULT 'string',
                    description TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de métricas de performance
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_unit TEXT,
                    measurement_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    component TEXT,
                    additional_metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índices para otimização
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp 
                ON sensor_readings(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sensor_readings_type 
                ON sensor_readings(sensor_type)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_motorcycle_detections_timestamp 
                ON motorcycle_detections(detection_timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_system_events_timestamp 
                ON system_events(timestamp)
            ''')
            
            conn.commit()
            self.logger.info("Banco de dados inicializado com sucesso")
            
            # Inserir configurações padrão
            self.setup_default_config()
    
    def setup_default_config(self):
        """Configura valores padrão do sistema"""
        default_configs = [
            ('detection_confidence_threshold', '0.5', 'float', 'Limite mínimo de confiança para detecções'),
            ('max_detections_per_frame', '10', 'int', 'Máximo de detecções por frame'),
            ('sensor_timeout_seconds', '30', 'int', 'Timeout para sensores offline'),
            ('data_retention_days', '30', 'int', 'Dias para manter dados históricos'),
            ('alert_temperature_max', '35.0', 'float', 'Temperatura máxima antes de alerta'),
            ('alert_humidity_max', '80.0', 'float', 'Umidade máxima antes de alerta'),
            ('system_name', 'IoT Motorcycle Detection System', 'string', 'Nome do sistema'),
            ('version', '1.0.0', 'string', 'Versão do sistema')
        ]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for key, value, config_type, description in default_configs:
                cursor.execute('''
                    INSERT OR IGNORE INTO system_config 
                    (config_key, config_value, config_type, description)
                    VALUES (?, ?, ?, ?)
                ''', (key, value, config_type, description))
            conn.commit()
    
    def insert_sensor_reading(self, sensor_data):
        """Insere leitura de sensor no banco de dados"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO sensor_readings 
                    (sensor_id, sensor_type, value, unit, timestamp, location_zone, 
                     latitude, longitude, battery_level, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    sensor_data.get('sensor_id'),
                    sensor_data.get('sensor_type'),
                    sensor_data.get('value'),
                    sensor_data.get('unit'),
                    sensor_data.get('timestamp', datetime.now().isoformat()),
                    sensor_data.get('location', {}).get('zone'),
                    sensor_data.get('location', {}).get('coordinates', [None, None])[0],
                    sensor_data.get('location', {}).get('coordinates', [None, None])[1],
                    sensor_data.get('battery_level'),
                    sensor_data.get('status', 'online')
                ))
                
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            self.logger.error(f"Erro ao inserir leitura de sensor: {e}")
            return None
    
    def insert_motorcycle_detection(self, detection_data):
        """Insere detecção de motocicleta no banco de dados"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO motorcycle_detections 
                    (confidence_score, bbox_x, bbox_y, bbox_width, bbox_height,
                     object_class, image_path, video_frame, processing_time_ms, algorithm_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    detection_data.get('confidence'),
                    detection_data.get('bbox', [0, 0, 0, 0])[0],
                    detection_data.get('bbox', [0, 0, 0, 0])[1],
                    detection_data.get('bbox', [0, 0, 0, 0])[2],
                    detection_data.get('bbox', [0, 0, 0, 0])[3],
                    detection_data.get('class', 'motorcycle'),
                    detection_data.get('image_path'),
                    detection_data.get('frame_number'),
                    detection_data.get('processing_time'),
                    detection_data.get('algorithm', 'YOLO')
                ))
                
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            self.logger.error(f"Erro ao inserir detecção: {e}")
            return None
    
    def log_system_event(self, event_type, description, severity='INFO', component=None, additional_data=None):
        """Registra evento do sistema"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO system_events 
                    (event_type, event_description, severity_level, component, additional_data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    event_type,
                    description,
                    severity,
                    component,
                    json.dumps(additional_data) if additional_data else None
                ))
                
                conn.commit()
                self.logger.info(f"Evento registrado: {event_type} - {description}")
                return cursor.lastrowid
                
        except Exception as e:
            self.logger.error(f"Erro ao registrar evento: {e}")
            return None
    
    def record_performance_metric(self, metric_name, value, unit=None, component=None, metadata=None):
        """Registra métrica de performance"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO performance_metrics 
                    (metric_name, metric_value, metric_unit, component, additional_metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    metric_name,
                    value,
                    unit,
                    component,
                    json.dumps(metadata) if metadata else None
                ))
                
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            self.logger.error(f"Erro ao registrar métrica: {e}")
            return None
    
    def get_sensor_history(self, sensor_type=None, hours=24, limit=1000):
        """Obtém histórico de sensores"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT * FROM sensor_readings 
                    WHERE timestamp >= datetime('now', '-{} hours')
                '''.format(hours)
                
                params = []
                if sensor_type:
                    query += ' AND sensor_type = ?'
                    params.append(sensor_type)
                
                query += ' ORDER BY timestamp DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Erro ao obter histórico de sensores: {e}")
            return []
    
    def get_detection_history(self, hours=24, min_confidence=0.5, limit=1000):
        """Obtém histórico de detecções"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM motorcycle_detections 
                    WHERE detection_timestamp >= datetime('now', '-{} hours')
                    AND confidence_score >= ?
                    ORDER BY detection_timestamp DESC 
                    LIMIT ?
                '''.format(hours), (min_confidence, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Erro ao obter histórico de detecções: {e}")
            return []
    
    def get_system_statistics(self):
        """Obtém estatísticas gerais do sistema"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total de leituras de sensores (últimas 24h)
                cursor.execute('''
                    SELECT COUNT(*) as total_readings 
                    FROM sensor_readings 
                    WHERE timestamp >= datetime('now', '-24 hours')
                ''')
                stats['total_sensor_readings_24h'] = cursor.fetchone()['total_readings']
                
                # Total de detecções (últimas 24h)
                cursor.execute('''
                    SELECT COUNT(*) as total_detections 
                    FROM motorcycle_detections 
                    WHERE detection_timestamp >= datetime('now', '-24 hours')
                ''')
                stats['total_detections_24h'] = cursor.fetchone()['total_detections']
                
                # Detecções por hora (últimas 24h)
                cursor.execute('''
                    SELECT 
                        strftime('%H', detection_timestamp) as hour,
                        COUNT(*) as count
                    FROM motorcycle_detections 
                    WHERE detection_timestamp >= datetime('now', '-24 hours')
                    GROUP BY strftime('%H', detection_timestamp)
                    ORDER BY hour
                ''')
                stats['detections_by_hour'] = {row['hour']: row['count'] for row in cursor.fetchall()}
                
                # Sensores ativos
                cursor.execute('''
                    SELECT 
                        sensor_type,
                        COUNT(DISTINCT sensor_id) as active_count
                    FROM sensor_readings 
                    WHERE timestamp >= datetime('now', '-5 minutes')
                    GROUP BY sensor_type
                ''')
                stats['active_sensors'] = {row['sensor_type']: row['active_count'] for row in cursor.fetchall()}
                
                # Eventos de sistema (últimas 24h)
                cursor.execute('''
                    SELECT 
                        severity_level,
                        COUNT(*) as count
                    FROM system_events 
                    WHERE timestamp >= datetime('now', '-24 hours')
                    GROUP BY severity_level
                ''')
                stats['system_events_24h'] = {row['severity_level']: row['count'] for row in cursor.fetchall()}
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def export_data_to_csv(self, output_dir="exports", start_date=None, end_date=None):
        """Exporta dados para arquivos CSV"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Definir período padrão (última semana)
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=7)
            
            with self.get_connection() as conn:
                # Exportar leituras de sensores
                sensor_df = pd.read_sql_query('''
                    SELECT * FROM sensor_readings 
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp
                ''', conn, params=[start_date.isoformat(), end_date.isoformat()])
                
                sensor_file = os.path.join(output_dir, f"sensor_readings_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv")
                sensor_df.to_csv(sensor_file, index=False)
                
                # Exportar detecções
                detection_df = pd.read_sql_query('''
                    SELECT * FROM motorcycle_detections 
                    WHERE detection_timestamp BETWEEN ? AND ?
                    ORDER BY detection_timestamp
                ''', conn, params=[start_date.isoformat(), end_date.isoformat()])
                
                detection_file = os.path.join(output_dir, f"motorcycle_detections_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv")
                detection_df.to_csv(detection_file, index=False)
                
                # Exportar eventos do sistema
                events_df = pd.read_sql_query('''
                    SELECT * FROM system_events 
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp
                ''', conn, params=[start_date.isoformat(), end_date.isoformat()])
                
                events_file = os.path.join(output_dir, f"system_events_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv")
                events_df.to_csv(events_file, index=False)
                
                self.logger.info(f"Dados exportados para {output_dir}")
                return {
                    'sensor_readings': sensor_file,
                    'motorcycle_detections': detection_file,
                    'system_events': events_file
                }
                
        except Exception as e:
            self.logger.error(f"Erro ao exportar dados: {e}")
            return None
    
    def cleanup_old_data(self, retention_days=30):
        """Remove dados antigos conforme política de retenção"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Remover leituras antigas de sensores
                cursor.execute('''
                    DELETE FROM sensor_readings 
                    WHERE created_at < ?
                ''', (cutoff_date.isoformat(),))
                sensor_deleted = cursor.rowcount
                
                # Remover detecções antigas
                cursor.execute('''
                    DELETE FROM motorcycle_detections 
                    WHERE created_at < ?
                ''', (cutoff_date.isoformat(),))
                detection_deleted = cursor.rowcount
                
                # Remover eventos antigos (manter críticos)
                cursor.execute('''
                    DELETE FROM system_events 
                    WHERE created_at < ? AND severity_level NOT IN ('ERROR', 'CRITICAL')
                ''', (cutoff_date.isoformat(),))
                events_deleted = cursor.rowcount
                
                conn.commit()
                
                self.logger.info(f"Limpeza concluída: {sensor_deleted} leituras, {detection_deleted} detecções, {events_deleted} eventos removidos")
                
                # Registrar evento de limpeza
                self.log_system_event(
                    'data_cleanup',
                    f'Limpeza automática executada. Removidos: {sensor_deleted + detection_deleted + events_deleted} registros',
                    'INFO',
                    'database_manager',
                    {
                        'retention_days': retention_days,
                        'sensor_readings_deleted': sensor_deleted,
                        'detections_deleted': detection_deleted,
                        'events_deleted': events_deleted
                    }
                )
                
                return {
                    'sensor_readings_deleted': sensor_deleted,
                    'detections_deleted': detection_deleted,
                    'events_deleted': events_deleted
                }
                
        except Exception as e:
            self.logger.error(f"Erro na limpeza de dados: {e}")
            return None
    
    def get_config_value(self, key, default=None):
        """Obtém valor de configuração"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT config_value, config_type FROM system_config WHERE config_key = ?', (key,))
                result = cursor.fetchone()
                
                if result:
                    value, config_type = result
                    # Converter para tipo apropriado
                    if config_type == 'int':
                        return int(value)
                    elif config_type == 'float':
                        return float(value)
                    elif config_type == 'bool':
                        return value.lower() in ('true', '1', 'yes')
                    else:
                        return value
                else:
                    return default
                    
        except Exception as e:
            self.logger.error(f"Erro ao obter configuração {key}: {e}")
            return default
    
    def set_config_value(self, key, value, config_type='string', description=None):
        """Define valor de configuração"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO system_config 
                    (config_key, config_value, config_type, description, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (key, str(value), config_type, description, datetime.now().isoformat()))
                conn.commit()
                
                self.logger.info(f"Configuração atualizada: {key} = {value}")
                return True
                
        except Exception as e:
            self.logger.error(f"Erro ao definir configuração {key}: {e}")
            return False
    
    def vacuum_database(self):
        """Otimiza o banco de dados"""
        try:
            with self.get_connection() as conn:
                conn.execute('VACUUM')
                self.logger.info("Otimização do banco de dados concluída")
                return True
        except Exception as e:
            self.logger.error(f"Erro na otimização do banco: {e}")
            return False
    
    def get_sensor_summary(self, hours=24):
        """Obtém resumo dos dados de sensores"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                summary = {}
                
                # Estatísticas por tipo de sensor
                cursor.execute('''
                    SELECT 
                        sensor_type,
                        COUNT(*) as total_readings,
                        AVG(value) as avg_value,
                        MIN(value) as min_value,
                        MAX(value) as max_value,
                        MAX(timestamp) as last_reading
                    FROM sensor_readings 
                    WHERE timestamp >= datetime('now', '-{} hours')
                    GROUP BY sensor_type
                '''.format(hours))
                
                for row in cursor.fetchall():
                    summary[row['sensor_type']] = {
                        'total_readings': row['total_readings'],
                        'avg_value': round(row['avg_value'], 2) if row['avg_value'] else 0,
                        'min_value': row['min_value'],
                        'max_value': row['max_value'],
                        'last_reading': row['last_reading']
                    }
                
                return summary
                
        except Exception as e:
            self.logger.error(f"Erro ao obter resumo de sensores: {e}")
            return {}
    
    def get_detection_summary(self, hours=24):
        """Obtém resumo das detecções"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total de detecções
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_detections,
                        AVG(confidence_score) as avg_confidence,
                        MAX(confidence_score) as max_confidence,
                        COUNT(DISTINCT object_class) as unique_classes
                    FROM motorcycle_detections 
                    WHERE detection_timestamp >= datetime('now', '-{} hours')
                '''.format(hours))
                
                result = cursor.fetchone()
                
                # Detecções por classe
                cursor.execute('''
                    SELECT 
                        object_class,
                        COUNT(*) as count,
                        AVG(confidence_score) as avg_confidence
                    FROM motorcycle_detections 
                    WHERE detection_timestamp >= datetime('now', '-{} hours')
                    GROUP BY object_class
                    ORDER BY count DESC
                '''.format(hours))
                
                classes = {}
                for row in cursor.fetchall():
                    classes[row['object_class']] = {
                        'count': row['count'],
                        'avg_confidence': round(row['avg_confidence'], 3)
                    }
                
                return {
                    'total_detections': result['total_detections'],
                    'avg_confidence': round(result['avg_confidence'], 3) if result['avg_confidence'] else 0,
                    'max_confidence': result['max_confidence'],
                    'unique_classes': result['unique_classes'],
                    'classes': classes
                }
                
        except Exception as e:
            self.logger.error(f"Erro ao obter resumo de detecções: {e}")
            return {}
    
    def create_backup(self, backup_path=None):
        """Cria backup do banco de dados"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"backup_iot_system_{timestamp}.db"
            
            # Criar diretório de backup se não existir
            backup_dir = os.path.dirname(backup_path) or "backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copiar banco de dados
            shutil.copy2(self.db_path, backup_path)
            
            # Registrar evento
            self.log_system_event(
                'database_backup',
                f'Backup criado: {backup_path}',
                'INFO',
                'database_manager'
            )
            
            self.logger.info(f"Backup criado: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {e}")
            return None
    
    def restore_backup(self, backup_path):
        """Restaura backup do banco de dados"""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Arquivo de backup não encontrado: {backup_path}")
            
            # Criar backup atual antes de restaurar
            current_backup = self.create_backup(f"{self.db_path}.pre_restore")
            
            # Restaurar backup
            shutil.copy2(backup_path, self.db_path)
            
            # Registrar evento
            self.log_system_event(
                'database_restore',
                f'Backup restaurado: {backup_path}',
                'INFO',
                'database_manager'
            )
            
            self.logger.info(f"Backup restaurado: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao restaurar backup: {e}")
            return False
    
    def analyze_performance(self):
        """Analisa performance do banco de dados"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                analysis = {}
                
                # Tamanho do banco
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                analysis['database_size_mb'] = round(db_size / (1024 * 1024), 2)
                
                # Número de tabelas
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                analysis['table_count'] = cursor.fetchone()[0]
                
                # Contagem de registros por tabela
                tables = ['sensor_readings', 'motorcycle_detections', 'system_events', 'performance_metrics']
                analysis['record_counts'] = {}
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        analysis['record_counts'][table] = cursor.fetchone()[0]
                    except:
                        analysis['record_counts'][table] = 0
                
                # Índices
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
                analysis['index_count'] = cursor.fetchone()[0]
                
                return analysis
                
        except Exception as e:
            self.logger.error(f"Erro na análise de performance: {e}")
            return {}
    
    def get_alerts_data(self, severity=None, hours=24):
        """Obtém dados de alertas do sistema"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT * FROM system_events 
                    WHERE timestamp >= datetime('now', '-{} hours')
                '''.format(hours)
                
                params = []
                if severity:
                    query += ' AND severity_level = ?'
                    params.append(severity)
                
                query += ' ORDER BY timestamp DESC'
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Erro ao obter dados de alertas: {e}")
            return []
    
    def close_connection(self):
        """Fecha conexão com o banco de dados"""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                self.logger.info("Conexão com banco de dados fechada")
        except Exception as e:
            self.logger.error(f"Erro ao fechar conexão: {e}")


def test_database_operations():
    """Testa todas as operações do banco de dados"""
    print(" TESTANDO OPERAÇÕES DO BANCO DE DADOS")
    print("=" * 50)
    
    # Inicializar gerenciador
    db_manager = DatabaseManager("test_iot_complete.db")
    
    # 1. Teste de inserção de dados de sensor
    print("\n 1. Testando inserção de dados de sensor...")
    sensor_data = {
        'sensor_id': 'temp_001',
        'sensor_type': 'temperature',
        'value': 25.5,
        'unit': '°C',
        'location': {
            'zone': 'parking_entrance',
            'coordinates': [-23.5505, -46.6333]
        },
        'battery_level': 85,
        'status': 'online'
    }
    
    sensor_id = db_manager.insert_sensor_reading(sensor_data)
    print(f" Sensor inserido com ID: {sensor_id}")
    
    # 2. Teste de inserção de detecção
    print("\n 2. Testando inserção de detecção...")
    detection_data = {
        'confidence': 0.85,
        'bbox': [100, 150, 200, 180],
        'class': 'motorcycle',
        'algorithm': 'YOLOv4',
        'processing_time': 45.2
    }
    
    detection_id = db_manager.insert_motorcycle_detection(detection_data)
    print(f" Detecção inserida com ID: {detection_id}")
    
    # 3. Teste de eventos do sistema
    print("\n 3. Testando log de eventos...")
    event_id = db_manager.log_system_event(
        'system_test',
        'Teste completo do sistema',
        'INFO',
        'test_module',
        {'test_data': True, 'version': '1.0.0'}
    )
    print(f" Evento registrado com ID: {event_id}")
    
    # 4. Teste de métricas
    print("\n 4. Testando métricas de performance...")
    metric_id = db_manager.record_performance_metric(
        'test_metric',
        95.5,
        'percent',
        'test_component',
        {'test': True}
    )
    print(f" Métrica registrada com ID: {metric_id}")
    
    # 5. Teste de estatísticas
    print("\n 5. Obtendo estatísticas...")
    stats = db_manager.get_system_statistics()
    print("Estatísticas do sistema:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 6. Teste de resumos
    print("\n 6. Testando resumos...")
    sensor_summary = db_manager.get_sensor_summary()
    detection_summary = db_manager.get_detection_summary()
    
    print("Resumo de sensores:", sensor_summary)
    print("Resumo de detecções:", detection_summary)
    
    # 7. Teste de configurações
    print("\n 7. Testando configurações...")
    db_manager.set_config_value('test_config', 42, 'int', 'Configuração de teste')
    test_value = db_manager.get_config_value('test_config')
    print(f" Configuração teste: {test_value}")
    
    # 8. Teste de backup
    print("\n 8. Testando backup...")
    backup_path = db_manager.create_backup()
    if backup_path:
        print(f" Backup criado: {backup_path}")
    
    # 9. Teste de análise de performance
    print("\n 9. Análise de performance...")
    performance = db_manager.analyze_performance()
    print("Performance do banco:")
    for key, value in performance.items():
        print(f"  {key}: {value}")
    
    # 10. Teste de exportação
    print("\n 10. Testando exportação...")
    export_files = db_manager.export_data_to_csv("test_exports_complete")
    if export_files:
        print(" Arquivos exportados:")
        for file_type, file_path in export_files.items():
            print(f"  {file_type}: {file_path}")
    
    # 11. Teste de limpeza
    print("\n 11. Testando limpeza...")
    cleanup_result = db_manager.cleanup_old_data(retention_days=0)  # Limpar tudo para teste
    if cleanup_result:
        print(f" Limpeza concluída: {cleanup_result}")
    
    # 12. Otimização
    print("\n 12. Otimizando banco...")
    if db_manager.vacuum_database():
        print(" Otimização concluída")
    
    # 13. Teste de múltiplos sensores
    print("\n 13. Testando múltiplos sensores...")
    sensors_test = [
        {'sensor_id': 'hum_001', 'sensor_type': 'humidity', 'value': 65.2, 'unit': '%'},
        {'sensor_id': 'mot_001', 'sensor_type': 'motion', 'value': 1, 'unit': 'boolean'},
        {'sensor_id': 'light_001', 'sensor_type': 'light', 'value': 420.5, 'unit': 'lux'}
    ]
    
    for sensor in sensors_test:
        sensor_id = db_manager.insert_sensor_reading(sensor)
        print(f"   {sensor['sensor_type']}: ID {sensor_id}")
    
    # 14. Teste de múltiplas detecções
    print("\n 14. Testando múltiplas detecções...")
    detections_test = [
        {'confidence': 0.92, 'bbox': [50, 100, 150, 120], 'class': 'motorcycle'},
        {'confidence': 0.78, 'bbox': [200, 180, 180, 140], 'class': 'bicycle'},
        {'confidence': 0.65, 'bbox': [350, 220, 200, 160], 'class': 'motorcycle'}
    ]
    
    for detection in detections_test:
        detection_id = db_manager.insert_motorcycle_detection(detection)
        print(f"   {detection['class']}: ID {detection_id}, Confiança: {detection['confidence']}")
    
    # 15. Teste de alertas
    print("\n 15. Testando sistema de alertas...")
    alerts_test = [
        ('temperature_alert', 'Temperatura acima do limite', 'WARNING'),
        ('detection_alert', 'Múltiplas motocicletas detectadas', 'INFO'),
        ('system_error', 'Erro de comunicação com sensor', 'ERROR')
    ]
    
    for event_type, description, severity in alerts_test:
        alert_id = db_manager.log_system_event(event_type, description, severity, 'alert_system')
        print(f"   {severity}: {event_type} - ID {alert_id}")
    
    print("\n TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
    print("=" * 50)
    
    # Estatísticas finais
    final_stats = db_manager.get_system_statistics()
    print("\n ESTATÍSTICAS FINAIS:")
    for key, value in final_stats.items():
        print(f"  {key}: {value}")


def main():
    """Função principal para demonstração"""
    print(" Gerenciador de Banco de Dados IoT")
    print("=" * 40)
    
    print("Escolha uma opção:")
    print("1. Executar testes completos")
    print("2. Inicializar banco em modo produção")
    print("3. Criar backup do banco existente")
    print("4. Analisar performance do banco")
    print("5. Exportar dados")
    print("6. Ver histórico de sensores")
    print("7. Ver estatísticas do sistema")
    print("8. Limpar dados antigos")
    print("9. Configurar sistema")
    print("0. Sair")
    
    try:
        choice = input("\nDigite sua escolha (0-9): ").strip()
        
        if choice == "1":
            test_database_operations()
            
        elif choice == "2":
            db_manager = DatabaseManager("iot_motorcycle_production.db")
            print(" Banco de dados de produção inicializado")
            
        elif choice == "3":
            db_manager = DatabaseManager()
            backup_path = db_manager.create_backup()
            if backup_path:
                print(f" Backup criado: {backup_path}")
            else:
                print(" Falha ao criar backup")
                
        elif choice == "4":
            db_manager = DatabaseManager()
            performance = db_manager.analyze_performance()
            print("\n ANÁLISE DE PERFORMANCE")
            print("-" * 30)
            for key, value in performance.items():
                print(f"{key}: {value}")
                
        elif choice == "5":
            db_manager = DatabaseManager()
            export_files = db_manager.export_data_to_csv()
            if export_files:
                print(" Dados exportados:")
                for file_type, file_path in export_files.items():
                    print(f"  {file_type}: {file_path}")
            else:
                print(" Falha na exportação")
                
        elif choice == "6":
            db_manager = DatabaseManager()
            print("\nTipos de sensor disponíveis: temperature, humidity, motion, light")
            sensor_type = input("Digite o tipo de sensor (ou Enter para todos): ").strip()
            
            if not sensor_type:
                sensor_type = None
                
            history = db_manager.get_sensor_history(sensor_type, hours=24, limit=10)
            
            if history:
                print(f"\n Últimas 10 leituras ({sensor_type or 'todos os sensores'}):")
                for reading in history:
                    print(f"  {reading['timestamp']}: {reading['sensor_type']} = {reading['value']} {reading['unit']}")
            else:
                print(" Nenhum dado encontrado")
                
        elif choice == "7":
            db_manager = DatabaseManager()
            stats = db_manager.get_system_statistics()
            sensor_summary = db_manager.get_sensor_summary()
            detection_summary = db_manager.get_detection_summary()
            
            print("\n ESTATÍSTICAS GERAIS:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
                
            print("\n RESUMO DE SENSORES:")
            for sensor_type, data in sensor_summary.items():
                print(f"  {sensor_type}: {data}")
                
            print("\n RESUMO DE DETECÇÕES:")
            for key, value in detection_summary.items():
                print(f"  {key}: {value}")
                
        elif choice == "8":
            db_manager = DatabaseManager()
            days = input("Quantos dias manter? (padrão: 30): ").strip()
            
            try:
                retention_days = int(days) if days else 30
            except ValueError:
                retention_days = 30
                
            print(f"Limpando dados com mais de {retention_days} dias...")
            result = db_manager.cleanup_old_data(retention_days)
            
            if result:
                print(" Limpeza concluída:")
                for key, value in result.items():
                    print(f"  {key}: {value}")
            else:
                print(" Falha na limpeza")
                
        elif choice == "9":
            db_manager = DatabaseManager()
            print("\n CONFIGURAÇÕES ATUAIS:")
            
            config_keys = [
                'detection_confidence_threshold',
                'max_detections_per_frame',
                'sensor_timeout_seconds',
                'data_retention_days'
            ]
            
            for key in config_keys:
                value = db_manager.get_config_value(key)
                print(f"  {key}: {value}")
            
            print("\nPara alterar uma configuração:")
            key = input("Nome da configuração: ").strip()
            if key:
                value = input("Novo valor: ").strip()
                config_type = input("Tipo (string/int/float/bool): ").strip() or 'string'
                
                if db_manager.set_config_value(key, value, config_type):
                    print(f" Configuração {key} atualizada para {value}")
                else:
                    print(" Falha ao atualizar configuração")
                    
        elif choice == "0":
            print(" Saindo...")
            return
            
        else:
            print(" Opção inválida")
            
    except KeyboardInterrupt:
        print("\n Operação cancelada pelo usuário")
    except Exception as e:
        print(f" Erro: {e}")
    
    # Perguntar se quer continuar
    if choice != "0":
        continue_choice = input("\nDeseja executar outra operação? (s/N): ").strip().lower()
        if continue_choice in ['s', 'sim', 'yes', 'y']:
            main()


if __name__ == "__main__":
    main()