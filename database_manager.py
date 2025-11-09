"""
Database Manager - Integração com Visão Computacional
"""
import sys
sys.path.append('database')

from database_module import (
    Database, DatabaseConfig,
    MotoRepository, LocalizacaoRepository, 
    AlertaRepository, SensorRepository
)
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar conexão
config = DatabaseConfig()
config.HOST = os.getenv('DB_HOST', 'localhost')
config.PORT = int(os.getenv('DB_PORT', 5432))
config.DATABASE = os.getenv('DB_NAME', 'mottu_tracking')
config.USER = os.getenv('DB_USER', 'mottu_user')
config.PASSWORD = os.getenv('DB_PASSWORD', 'mottu123')

# Inicializar database
db = Database(config)

# Repositórios disponíveis
moto_repo = MotoRepository(db)
loc_repo = LocalizacaoRepository(db)
alerta_repo = AlertaRepository(db)
sensor_repo = SensorRepository(db)

print("✅ Database Manager carregado com sucesso!")

# Função auxiliar para salvar detecção
def salvar_deteccao_moto(placa, latitude, longitude, confianca=0.9):
    """
    Salva detecção de moto no banco de dados
    """
    try:
        # Buscar moto pela placa
        motos = moto_repo.listar_motos()
        moto = next((m for m in motos if m['placa'] == placa), None)
        
        if not moto:
            # Criar moto se não existir
            moto_id = moto_repo.criar_moto(
                placa=placa,
                modelo="Moto Detectada",
                marca="Desconhecida",
                ano=2024
            )
            print(f"✅ Nova moto criada: {placa} (ID: {moto_id})")
        else:
            moto_id = moto['id']
        
        # Registrar localização
        loc_repo.registrar_localizacao(
            moto_id=moto_id,
            latitude=latitude,
            longitude=longitude,
            velocidade=0,
            origem='visao_computacional'
        )
        
        print(f"✅ Localização de {placa} salva no banco!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar detecção: {e}")
        return False