"""
Teste simples do banco de dados
"""
from database_manager import moto_repo, loc_repo, db

print("🧪 Testando banco de dados...")

# Teste 1: Criar moto
try:
    moto_id = moto_repo.criar_moto(
        placa="TEST123",
        modelo="Honda CG 160",
        marca="Honda",
        ano=2023
    )
    print(f"✅ Teste 1 OK - Moto criada: ID {moto_id}")
except Exception as e:
    print(f"❌ Teste 1 FALHOU: {e}")

# Teste 2: Listar motos
try:
    motos = moto_repo.listar_motos()
    print(f"✅ Teste 2 OK - {len(motos)} motos encontradas")
    for moto in motos[:3]:
        print(f"   - {moto['placa']}: {moto['modelo']}")
except Exception as e:
    print(f"❌ Teste 2 FALHOU: {e}")

# Teste 3: Registrar localização
try:
    loc_repo.registrar_localizacao(
        moto_id=1,
        latitude=-23.5505,
        longitude=-46.6333,
        velocidade=45.5,
        origem='teste'
    )
    print(f"✅ Teste 3 OK - Localização registrada")
except Exception as e:
    print(f"❌ Teste 3 FALHOU: {e}")

print("\n🎉 Testes concluídos!")
db.close_all_connections()