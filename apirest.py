"""
API REST - Mottu Tracking System
Flask API para integração com Mobile App, Java, .NET, etc.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from typing import Dict, List
import logging
from database_module import (
    Database, DatabaseConfig,
    MotoRepository, LocalizacaoRepository, AlertaRepository,
    ViagemRepository, SensorRepository, DashboardRepository
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__)
CORS(app)  # Permitir CORS para integração com apps externos

# Configurar banco de dados
config = DatabaseConfig()
config.HOST = "localhost"
config.DATABASE = "mottu_tracking"
config.USER = "postgres"
config.PASSWORD = "sua_senha"

db = Database(config)

# Inicializar repositórios
moto_repo = MotoRepository(db)
loc_repo = LocalizacaoRepository(db)
alerta_repo = AlertaRepository(db)
viagem_repo = ViagemRepository(db)
sensor_repo = SensorRepository(db)
dashboard_repo = DashboardRepository(db)


# ============================================
# ENDPOINTS - MOTOS
# ============================================

@app.route('/api/motos', methods=['GET'])
def listar_motos():
    """Lista todas as motos ou filtra por status"""
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        
        motos = moto_repo.listar_motos(status=status, limit=limit)
        
        return jsonify({
            'success': True,
            'data': motos,
            'count': len(motos)
        }), 200
    except Exception as e:
        logger.error(f"Erro ao listar motos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/motos/<int:moto_id>', methods=['GET'])
def obter_moto(moto_id):
    """Obtém informações de uma moto específica"""
    try:
        moto = moto_repo.obter_moto(moto_id)
        
        if not moto:
            return jsonify({'success': False, 'error': 'Moto não encontrada'}), 404
        
        return jsonify({'success': True, 'data': moto}), 200
    except Exception as e:
        logger.error(f"Erro ao obter moto: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/motos', methods=['POST'])
def criar_moto():
    """Cria uma nova moto"""
    try:
        dados = request.get_json()
        
        # Validação básica
        campos_obrigatorios = ['placa', 'modelo', 'marca', 'ano']
        for campo in campos_obrigatorios:
            if campo not in dados:
                return jsonify({
                    'success': False, 
                    'error': f'Campo obrigatório: {campo}'
                }), 400
        
        moto_id = moto_repo.criar_moto(
            placa=dados['placa'],
            modelo=dados['modelo'],
            marca=dados['marca'],
            ano=dados['ano'],
            cor=dados.get('cor'),
            numero_chassi=dados.get('numero_chassi'),
            status=dados.get('status', 'disponivel')
        )
        
        return jsonify({
            'success': True,
            'data': {'id': moto_id},
            'message': 'Moto criada com sucesso'
        }), 201
    except Exception as e:
        logger.error(f"Erro ao criar moto: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/motos/<int:moto_id>/status', methods=['PUT'])
def atualizar_status_moto(moto_id):
    """Atualiza o status de uma moto"""
    try:
        dados = request.get_json()
        novo_status = dados.get('status')
        
        if not novo_status:
            return jsonify({'success': False, 'error': 'Status não fornecido'}), 400
        
        sucesso = moto_repo.atualizar_status(moto_id, novo_status)
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': 'Status atualizado com sucesso'
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Moto não encontrada'}), 404
    except Exception as e:
        logger.error(f"Erro ao atualizar status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/motos/<int:moto_id>/bateria', methods=['PUT'])
def atualizar_bateria(moto_id):
    """Atualiza o nível de bateria da moto"""
    try:
        dados = request.get_json()
        percentual = dados.get('percentual')
        
        if percentual is None or not (0 <= percentual <= 100):
            return jsonify({
                'success': False,
                'error': 'Percentual deve estar entre 0 e 100'
            }), 400
        
        sucesso = moto_repo.atualizar_bateria(moto_id, percentual)
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': 'Bateria atualizada com sucesso'
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Moto não encontrada'}), 404
    except Exception as e:
        logger.error(f"Erro ao atualizar bateria: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# ENDPOINTS - LOCALIZAÇÃO
# ============================================

@app.route('/api/localizacoes', methods=['GET'])
def obter_todas_localizacoes():
    """Obtém localização atual de todas as motos"""
    try:
        localizacoes = loc_repo.obter_todas_localizacoes_atuais()
        
        return jsonify({
            'success': True,
            'data': localizacoes,
            'count': len(localizacoes)
        }), 200
    except Exception as e:
        logger.error(f"Erro ao obter localizações: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/motos/<int:moto_id>/localizacao', methods=['GET'])
def obter_localizacao_moto(moto_id):
    """Obtém localização atual de uma moto"""
    try:
        localizacao = loc_repo.obter_localizacao_atual(moto_id)
        
        if not localizacao:
            return jsonify({
                'success': False,
                'error': 'Localização não encontrada'
            }), 404
        
        return jsonify({'success': True, 'data': localizacao}), 200
    except Exception as e:
        logger.error(f"Erro ao obter localização: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/motos/<int:moto_id>/localizacao/historico', methods=['GET'])
def obter_historico_localizacao(moto_id):
    """Obtém histórico de localizações de uma moto"""
    try:
        horas = int(request.args.get('horas', 24))
        historico = loc_repo.obter_historico(moto_id, horas)
        
        return jsonify({
            'success': True,
            'data': historico,
            'count': len(historico)
        }), 200
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/localizacoes', methods=['POST'])
def registrar_localizacao():
    """Registra nova localização de uma moto (endpoint para IoT/Visão Computacional)"""
    try:
        dados = request.get_json()
        
        # Validação
        campos_obrigatorios = ['moto_id', 'latitude', 'longitude']
        for campo in campos_obrigatorios:
            if campo not in dados:
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório: {campo}'
                }), 400
        
        loc_id = loc_repo.registrar_localizacao(
            moto_id=dados['moto_id'],
            latitude=dados['latitude'],
            longitude=dados['longitude'],
            velocidade=dados.get('velocidade', 0),
            origem=dados.get('origem', 'iot'),
            direcao=dados.get('direcao'),
            precisao=dados.get('precisao'),
            altitude=dados.get('altitude')
        )
        
        return jsonify({
            'success': True,
            'data': {'id': loc_id},
            'message': 'Localização registrada com sucesso'
        }), 201
    except Exception as e:
        logger.error(f"Erro ao registrar localização: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# ENDPOINTS - ALERTAS
# ============================================

@app.route('/api/alertas', methods=['GET'])
def listar_alertas():
    """Lista alertas ativos"""
    try:
        severidade = request.args.get('severidade')
        alertas = alerta_repo.listar_alertas_ativos(severidade)
        
        return jsonify({
            'success': True,
            'data': alertas,
            'count': len(alertas)
        }), 200
    except Exception as e:
        logger.error(f"Erro ao listar alertas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alertas', methods=['POST'])
def criar_alerta():
    """Cria um novo alerta"""
    try:
        dados = request.get_json()
        
        if 'tipo' not in dados or 'mensagem' not in dados:
            return jsonify({
                'success': False,
                'error': 'Tipo e mensagem são obrigatórios'
            }), 400
        
        alerta_id = alerta_repo.criar_alerta(
            moto_id=dados.get('moto_id'),
            tipo=dados['tipo'],
            mensagem=dados['mensagem'],
            severidade=dados.get('severidade', 'media'),
            detalhes=dados.get('detalhes')
        )
        
        return jsonify({
            'success': True,
            'data': {'id': alerta_id},
            'message': 'Alerta criado com sucesso'
        }), 201
    except Exception as e:
        logger.error(f"Erro ao criar alerta: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alertas/<int:alerta_id>/resolver', methods=['PUT'])
def resolver_alerta(alerta_id):
    """Marca um alerta como resolvido"""
    try:
        dados = request.get_json()
        resolvido_por = dados.get('resolvido_por', 'Sistema')
        
        sucesso = alerta_repo.resolver_alerta(alerta_id, resolvido_por)
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': 'Alerta resolvido com sucesso'
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Alerta não encontrado'}), 404
    except Exception as e:
        logger.error(f"Erro ao resolver alerta: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# ENDPOINTS - VIAGENS
# ============================================

@app.route('/api/viagens/ativas', methods=['GET'])
def listar_viagens_ativas():
    """Lista viagens em andamento"""
    try:
        viagens = viagem_repo.listar_viagens_ativas()
        
        return jsonify({
            'success': True,
            'data': viagens,
            'count': len(viagens)
        }), 200
    except Exception as e:
        logger.error(f"Erro ao listar viagens: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/viagens', methods=['POST'])
def iniciar_viagem():
    """Inicia uma nova viagem"""
    try:
        dados = request.get_json()
        
        campos_obrigatorios = ['moto_id', 'entregador_id', 'origem_latitude', 'origem_longitude']
        for campo in campos_obrigatorios:
            if campo not in dados:
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório: {campo}'
                }), 400
        
        viagem_id = viagem_repo.iniciar_viagem(
            moto_id=dados['moto_id'],
            entregador_id=dados['entregador_id'],
            origem_lat=dados['origem_latitude'],
            origem_lon=dados['origem_longitude']
        )
        
        return jsonify({
            'success': True,
            'data': {'id': viagem_id},
            'message': 'Viagem iniciada com sucesso'
        }), 201
    except Exception as e:
        logger.error(f"Erro ao iniciar viagem: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/viagens/<int:viagem_id>/finalizar', methods=['PUT'])
def finalizar_viagem(viagem_id):
    """Finaliza uma viagem"""
    try:
        dados = request.get_json()
        
        campos_obrigatorios = ['destino_latitude', 'destino_longitude', 'distancia_km', 'valor']
        for campo in campos_obrigatorios:
            if campo not in dados:
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório: {campo}'
                }), 400
        
        sucesso = viagem_repo.finalizar_viagem(
            viagem_id=viagem_id,
            destino_lat=dados['destino_latitude'],
            destino_lon=dados['destino_longitude'],
            distancia_km=dados['distancia_km'],
            valor=dados['valor']
        )
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': 'Viagem finalizada com sucesso'
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Viagem não encontrada'}), 404
    except Exception as e:
        logger.error(f"Erro ao finalizar viagem: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# ENDPOINTS - SENSORES IOT
# ============================================

@app.route('/api/sensores', methods=['POST'])
def registrar_leitura_sensor():
    """Registra leitura de sensor IoT"""
    try:
        dados = request.get_json()
        
        campos_obrigatorios = ['moto_id', 'tipo_sensor', 'valor']
        for campo in campos_obrigatorios:
            if campo not in dados:
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório: {campo}'
                }), 400
        
        sensor_id = sensor_repo.registrar_leitura(
            moto_id=dados['moto_id'],
            tipo_sensor=dados['tipo_sensor'],
            valor=dados['valor'],
            unidade=dados.get('unidade'),
            metadata=dados.get('metadata')
        )
        
        return jsonify({
            'success': True,
            'data': {'id': sensor_id},
            'message': 'Leitura registrada com sucesso'
        }), 201
    except Exception as e:
        logger.error(f"Erro ao registrar leitura: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/motos/<int:moto_id>/sensores/<tipo_sensor>', methods=['GET'])
def obter_leituras_sensor(moto_id, tipo_sensor):
    """Obtém últimas leituras de um sensor"""
    try:
        limite = int(request.args.get('limite', 10))
        leituras = sensor_repo.obter_ultimas_leituras(moto_id, tipo_sensor, limite)
        
        return jsonify({
            'success': True,
            'data': leituras,
            'count': len(leituras)
        }), 200
    except Exception as e:
        logger.error(f"Erro ao obter leituras: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# ENDPOINTS - DASHBOARD
# ============================================

@app.route('/api/dashboard/resumo', methods=['GET'])
def obter_resumo_dashboard():
    """Obtém resumo para o dashboard"""
    try:
        resumo = dashboard_repo.obter_resumo()
        
        return jsonify({'success': True, 'data': resumo}), 200
    except Exception as e:
        logger.error(f"Erro ao obter resumo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/dashboard/estatisticas', methods=['GET'])
def obter_estatisticas():
    """Obtém estatísticas de uso das motos"""
    try:
        estatisticas = dashboard_repo.obter_estatisticas_motos()
        
        return jsonify({
            'success': True,
            'data': estatisticas,
            'count': len(estatisticas)
        }), 200
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/dashboard/motos-alertas', methods=['GET'])
def obter_motos_alertas():
    """Obtém motos com alertas ativos"""
    try:
        motos = dashboard_repo.obter_motos_com_alertas()
        
        return jsonify({
            'success': True,
            'data': motos,
            'count': len(motos)
        }), 200
    except Exception as e:
        logger.error(f"Erro ao obter motos com alertas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# ENDPOINT - HEALTH CHECK
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica se a API está funcionando"""
    return jsonify({
        'success': True,
        'message': 'API Mottu Tracking está funcionando',
        'timestamp': datetime.now().isoformat()
    }), 200


# ============================================
# TRATAMENTO DE ERROS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint não encontrado'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500


# ============================================
# EXECUTAR APLICAÇÃO
# ============================================

if __name__ == '__main__':
    print("=" * 50)
    print("API REST - Mottu Tracking System")
    print("=" * 50)
    print("Endpoints disponíveis:")
    print("  - GET  /api/motos")
    print("  - POST /api/motos")
    print("  - GET  /api/localizacoes")
    print("  - POST /api/localizacoes")
    print("  - GET  /api/alertas")
    print("  - POST /api/alertas")
    print("  - GET  /api/viagens/ativas")
    print("  - POST /api/sensores")
    print("  - GET  /api/dashboard/resumo")
    print("=" * 50)
    
    # Executar em modo de desenvolvimento
    app.run(host='0.0.0.0', port=5000, debug=True)