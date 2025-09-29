# 📡 Documentação da API - MotoScan

## 🔗 Base URL
http://localhost:5000

## 📋 Endpoints Principais

### 1. Upload e Análise de Imagem
**POST** `/upload`

#### Response
```json
{
  "success": true,
  "results": {
    "modelo": "Mottu Sport 110i",
    "placa": "ABC-1234",
    "estado": "bom",
    "localizacao": "Setor A"
  }
}
