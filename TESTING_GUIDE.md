# 🧪 GUIA DE TESTES PÓS-REFATORAÇÃO

## 1. Verificar Imports

### Linux/Mac (Bash)

#### Upload Service
```bash
cd services/upload
python -m py_compile app/main.py app/routes.py app/celery_app.py
```

#### Processor Service
```bash
cd services/processor
python -m py_compile app/main.py app/celery_app.py
```

#### Reports Service
```bash
cd services/reports
python -m py_compile app/main.py
```

### Windows (PowerShell) ⭐

#### Upload Service
```powershell
cd services/upload
python -m py_compile app/main.py app/routes.py app/celery_app.py
if ($LASTEXITCODE -eq 0) { Write-Host "✅ Upload Service OK" -ForegroundColor Green } else { Write-Host "❌ Upload Service ERROR" -ForegroundColor Red }
```

#### Processor Service
```powershell
cd services/processor
python -m py_compile app/main.py app/celery_app.py
if ($LASTEXITCODE -eq 0) { Write-Host "✅ Processor Service OK" -ForegroundColor Green } else { Write-Host "❌ Processor Service ERROR" -ForegroundColor Red }
```

#### Reports Service
```powershell
cd services/reports
python -m py_compile app/main.py
if ($LASTEXITCODE -eq 0) { Write-Host "✅ Reports Service OK" -ForegroundColor Green } else { Write-Host "❌ Reports Service ERROR" -ForegroundColor Red }
```

#### Todos os Serviços (One-Liner)
```powershell
cd services/upload; python -m py_compile app/main.py; cd ../processor; python -m py_compile app/main.py; cd ../reports; python -m py_compile app/main.py; cd ../..
Write-Host "✅ Todos os imports validados" -ForegroundColor Green
```

---

## 2. Verificar Dependências

### Linux/Mac (Bash)

#### Install shared
```bash
cd shared
pip install -e .
```

#### Install services (with shared as dependency)
```bash
cd services/upload && pip install -e .
cd ../processor && pip install -e .
cd ../reports && pip install -e .
```

### Windows (PowerShell) ⭐

#### Install shared
```powershell
cd shared
pip install -e .
Write-Host "✅ Shared instalado" -ForegroundColor Green
```

#### Install services (with shared as dependency)
```powershell
cd services/upload
pip install -e .
Write-Host "✅ Upload instalado" -ForegroundColor Green

cd ../processor
pip install -e .
Write-Host "✅ Processor instalado" -ForegroundColor Green

cd ../reports
pip install -e .
Write-Host "✅ Reports instalado" -ForegroundColor Green

cd ../..
```

#### Install tudo (One-Liner)
```powershell
cd shared; pip install -e . | Out-Null; cd ../services/upload; pip install -e . | Out-Null; cd ../processor; pip install -e . | Out-Null; cd ../reports; pip install -e . | Out-Null; cd ../../..
Write-Host "✅ Todas as dependências instaladas" -ForegroundColor Green
```

---

## 3. Testar Bancos de Dados

### Linux/Mac (Bash)

#### Iniciar containers
```bash
docker-compose up -d postgres redis minio
```

#### Verificar bancos criados
```bash
psql -U app -h localhost -c "\l"
```

**Expected:**
```
upload_db   | app | UTF8
reports_db  | app | UTF8
```

#### Conectar e verificar tabelas (após start dos serviços)
```bash
psql -U app -h localhost -d upload_db
SELECT * FROM analyses;

psql -U app -h localhost -d reports_db
SELECT * FROM analyses;
```

### Windows (PowerShell) ⭐

#### Iniciar containers
```powershell
docker-compose up -d postgres redis minio
Write-Host "✅ Containers iniciados" -ForegroundColor Green
Start-Sleep -Seconds 3
```

#### Verificar bancos criados (via docker exec)
```powershell
$databases = docker exec tech-challenge-5-postgres-1 psql -U app -t -c "\l" | grep -E "upload_db|reports_db"
Write-Host $databases
Write-Host "✅ Bancos verificados" -ForegroundColor Green
```

#### Verificar bancos criados (alternativo)
```powershell
docker exec tech-challenge-5-postgres-1 psql -U app -c "\l+" | Select-String "upload_db|reports_db"
```

#### Conectar e verificar tabelas (após start dos serviços)
```powershell
# Query upload_db
docker exec tech-challenge-5-postgres-1 psql -U app -d upload_db -c "SELECT * FROM analyses LIMIT 5;"

# Query reports_db
docker exec tech-challenge-5-postgres-1 psql -U app -d reports_db -c "SELECT * FROM analyses LIMIT 5;"
```

---

## 4. Testar Services

### Linux/Mac (Bash)

#### Start completo
```bash
docker-compose up
```

#### Logs em tempo real
```bash
docker-compose logs -f upload processor reports
```

### Windows (PowerShell) ⭐

#### Start completo
```powershell
docker-compose up
```

#### Logs em tempo real (em nova janela PowerShell)
```powershell
docker-compose logs -f upload processor reports
```

#### Logs apenas de um serviço
```powershell
docker-compose logs -f upload      # Logs do Upload
docker-compose logs -f processor   # Logs do Processor
docker-compose logs -f reports     # Logs do Reports
```

#### Monitorar health dos containers
```powershell
while ($true) {
    Clear-Host
    Write-Host "=== Docker Compose Status ===" -ForegroundColor Cyan
    docker-compose ps
    Write-Host "`nÚltimas 3 linhas de cada log:`n"
    docker-compose logs --tail=3 upload
    Write-Host ""
    docker-compose logs --tail=3 processor
    Write-Host ""
    docker-compose logs --tail=3 reports
    Start-Sleep -Seconds 5
}
```

---

## 5. Testar API

### Linux/Mac (Bash)

#### Upload um arquivo
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@seu_arquivo.png"
```

**Expected Response:**
```json
{
  "id": "uuid-string",
  "filename": "seu_arquivo.png",
  "file_ref": "uploads/uuid/seu_arquivo.png",
  "status": "received",
  "error_message": null,
  "created_at": "2026-05-10T...",
  "updated_at": "2026-05-10T..."
}
```

#### Monitorar processamento
```bash
# Terminal 1: Watch processor logs
docker-compose logs -f processor

# Terminal 2: Poll status (wait ~30s for processing)
curl http://localhost:8000/api/v1/report/{ANALYSIS_ID}
```

### Windows (PowerShell) ⭐

#### Upload um arquivo
```powershell
# Método 1: usando curl (Windows 10+)
curl.exe -X POST http://localhost:8000/api/v1/upload `
-F "file=@test.png"

# Método 2: usando Invoke-WebRequest (PowerShell nativo)
$fileBytes = [System.IO.File]::ReadAllBytes("seu_arquivo.png")
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

$body = (
    "--$boundary$LF",
    "Content-Disposition: form-data; name=`"file`"; filename=`"seu_arquivo.png`"$LF",
    "Content-Type: image/png$LF$LF"
) -join "" + [System.Text.Encoding]::GetEncoding("iso-8859-1").GetString($fileBytes) + "$LF--$boundary--$LF"

$response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/upload" `
  -Method Post `
  -ContentType "multipart/form-data; boundary=$boundary" `
  -Body $body

$response.Content | ConvertFrom-Json | Format-Table
```

**Expected Response:**
```json
{
  "id": "uuid-string",
  "filename": "seu_arquivo.png",
  "file_ref": "uploads/uuid/seu_arquivo.png",
  "status": "received"
}
```

#### Monitorar processamento (PowerShell)
```powershell
# Terminal 1: Watch processor logs
docker-compose logs -f processor

# Terminal 2: Poll status (em nova aba PowerShell)
$analysisId = "UUID_DO_UPLOAD_ACIMA"

# Loop para monitorar status
for ($i = 0; $i -lt 60; $i++) {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/report/$analysisId" `
      -Method Get | ConvertFrom-Json
    
    Write-Host "Tentativa $($i+1): Status = $($response.status ?? 'error')" -ForegroundColor Cyan
    
    if ($response.status -eq "analyzed") {
        Write-Host "✅ Análise concluída!" -ForegroundColor Green
        $response | Format-Table
        break
    }
    
    Start-Sleep -Seconds 1
}
```

#### Upload e monitorar (One-Liner)
```powershell
# Upload
$upload = curl.exe -X POST http://localhost:8000/api/v1/upload -F "file=@seu_arquivo.png" | ConvertFrom-Json
$id = $upload.id
Write-Host "✅ Upload concluído: $id" -ForegroundColor Green

# Aguardar 30s
Start-Sleep -Seconds 30

# Verificar resultado
$report = curl.exe -X GET "http://localhost:8000/api/v1/report/$id" | ConvertFrom-Json
Write-Host "Status: $($report.status)" -ForegroundColor Cyan
$report | Format-Table
```

---

## 6. Testar Shared Module

### Linux/Mac (Bash)

#### Verificar imports funcionam
```bash
python3 << 'EOF'
from shared.database import Base, SessionLocal, get_db, init_db
from shared.models import Analysis
from shared.storage import upload_file, download_file, encode_image
from shared.config import BaseConfig
from shared.celery import create_celery_app

print("✅ Todos os imports de shared funcionam!")
EOF
```

### Windows (PowerShell) ⭐

#### Verificar imports funcionam
```powershell
python << 'EOF'
from shared.database import Base, SessionLocal, get_db, init_db
from shared.models import Analysis
from shared.storage import upload_file, download_file, encode_image
from shared.config import BaseConfig
from shared.celery import create_celery_app

print("✅ Todos os imports de shared funcionam!")
EOF
```

#### Verificar imports (alternativo com script)
```powershell
$pythonCode = @"
try:
    from shared.database import Base, SessionLocal, get_db, init_db
    from shared.models import Analysis
    from shared.storage import upload_file, download_file, encode_image
    from shared.config import BaseConfig
    from shared.celery import create_celery_app
    print("✅ Todos os imports funcionam!")
except Exception as e:
    print(f"❌ Erro: {e}")
"@

$pythonCode | python
```

#### Verificar estrutura de shared
```powershell
Get-ChildItem shared/src/shared/ -Filter "*.py" | ForEach-Object {
    Write-Host "✅ $($_.Name)" -ForegroundColor Green
}
```

---

## 7. Troubleshooting

### Linux/Mac (Bash)

#### Se database não inicializa:
```bash
# Verificar logs
docker logs tech-challenge-5-postgres-1

# Reset de dados
docker-compose down -v
docker-compose up postgres  # Recria bancos via init.sql
```

#### Se processor não processa:
```bash
# Verificar celery
docker logs tech-challenge-5-processor-1

# Verificar Redis
docker-compose exec redis redis-cli PING
# Expected: PONG

# Verificar fila
docker-compose exec redis redis-cli LLEN celery
```

#### Se reports não retorna dados:
```bash
# Verificar se análise está em status "analyzed"
psql -U app -h localhost -d upload_db
SELECT id, status, result_data FROM analyses;

# Se result_data é NULL, processor ainda está processando
```

### Windows (PowerShell) ⭐

#### Se database não inicializa:
```powershell
# Verificar logs
docker logs tech-challenge-5-postgres-1

# Reset de dados (ATENÇÃO: Apaga banco!)
docker-compose down -v
docker-compose up postgres  # Recria bancos via init.sql
```

#### Se processor não processa:
```powershell
# Verificar celery
docker logs tech-challenge-5-processor-1

# Verificar Redis
docker exec tech-challenge-5-redis-1 redis-cli PING
# Expected: PONG

# Verificar fila Celery
docker exec tech-challenge-5-redis-1 redis-cli LLEN celery
docker exec tech-challenge-5-redis-1 redis-cli KEYS "*"  # Ver todas as keys
```

#### Se reports não retorna dados:
```powershell
# Verificar se análise está em status "analyzed"
docker exec tech-challenge-5-postgres-1 psql -U app -d upload_db -c `
  "SELECT id, status, result_data FROM analyses ORDER BY created_at DESC LIMIT 5;"

# Se result_data é NULL, processor ainda está processando
```

#### Listar containers e status
```powershell
docker-compose ps
docker-compose ps --format table
```

#### Ver logs de todos os serviços
```powershell
docker-compose logs --tail=50  # Últimas 50 linhas

# Apenas de um serviço
docker-compose logs --tail=50 upload
docker-compose logs --tail=50 processor
docker-compose logs --tail=50 reports
```

#### Reiniciar um serviço específico
```powershell
docker-compose restart upload
docker-compose restart processor
docker-compose restart reports
```

#### Limpar dados (ATENÇÃO!)
```powershell
# Apagar TUDO
docker-compose down -v

# Apenas containers (mantém volumes)
docker-compose down

# Apenas parar sem apagar
docker-compose stop
```

---

## 8. Validação Final - Checklist

- [ ] `docker-compose up` sobe sem erros
- [ ] 3 bancos criados (upload_db, reports_db)
- [ ] Upload de arquivo retorna 202 ACCEPTED
- [ ] Arquivo armazenado em MinIO
- [ ] Processor celery inicia sem erros
- [ ] Após ~30s, status muda para "analyzed"
- [ ] GET /reports/{id} retorna dados processados
- [ ] Logs não mostram erro de import
- [ ] Não há avisos de database locking

---

## 9. Performance Check

### Verificar duplicação eliminada
```bash
# Contar linhas antes (no git):
git show HEAD:services/upload/app/database.py | wc -l
git show HEAD:services/processor/app/database.py | wc -l

# Contar linhas depois (local):
wc -l shared/src/shared/database.py

# Expected: 1 arquivo de ~30 linhas vs 2 de 17 linhas cada
```

### Verificar imports
```bash
# Listar todos os imports de "app.database"
grep -r "from app.database import" services/

# Esperado: Apenas re-exports mínimos
```

---

## 10. Cleanup (Opcional)

### Remover dependências duplicadas dos services
```yaml
# services/upload/pyproject.toml
# Remover:
# - "minio>=7.2.0" (já em shared)
# - "sqlalchemy>=2.0.0" (já em shared)

# services/processor/pyproject.toml
# Remover:
# - "minio>=7.2.0" (já em shared)
# - "sqlalchemy>=2.0.0" (já em shared)

# services/reports/pyproject.toml
# Remover:
# - "minio>=7.2.0" (não usa!)
# - "sqlalchemy>=2.0.0" (já em shared)
```

---

## 11. Comandos Úteis PowerShell ⭐

### Desenvolvimento Rápido

#### Rebuild de um serviço
```powershell
docker-compose up -d --build upload
docker-compose up -d --build processor
docker-compose up -d --build reports
```

#### Rebuild de tudo
```powershell
docker-compose up -d --build
```

#### Ver tamanho das imagens
```powershell
docker images | Select-String "tech-challenge"
```

#### Limpar imagens não utilizadas
```powershell
docker image prune -f
```

### Debugging

#### Entrar em um container
```powershell
# Acessar shell do container
docker exec -it tech-challenge-5-upload-1 /bin/bash
docker exec -it tech-challenge-5-processor-1 /bin/bash
docker exec -it tech-challenge-5-reports-1 /bin/bash
```

#### Ver variáveis de ambiente
```powershell
docker exec tech-challenge-5-upload-1 env | Select-String "DATABASE|MINIO|REDIS"
```

#### Executar comando em container
```powershell
docker exec tech-challenge-5-upload-1 python -c "from app.config import settings; print(settings.database_url)"
```

### Monitoramento Avançado

#### Dashboard em tempo real (loop infinito)
```powershell
function Show-DockerDashboard {
    while ($true) {
        Clear-Host
        Write-Host "╔═══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║          TECH CHALLENGE 5 - Docker Status           ║" -ForegroundColor Cyan
        Write-Host "╚═══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
        Write-Host ""
        
        docker-compose ps | Format-Table
        
        Write-Host "`n=== Últimas linhas de log ===" -ForegroundColor Yellow
        Write-Host "`n--- Upload ---"
        docker-compose logs --tail=2 upload | Select-Object -Last 1
        
        Write-Host "`n--- Processor ---"
        docker-compose logs --tail=2 processor | Select-Object -Last 1
        
        Write-Host "`n--- Reports ---"
        docker-compose logs --tail=2 reports | Select-Object -Last 1
        
        Write-Host "`n[Próxima atualização em 5s... Pressione Ctrl+C para sair]" -ForegroundColor Gray
        Start-Sleep -Seconds 5
    }
}

# Usar:
# Show-DockerDashboard
```

#### Monitorar CPU/Memory
```powershell
docker stats --no-stream
```

#### Ver eventos docker
```powershell
docker events --filter "container=tech-challenge"
```

### Testes Automatizados

#### Script de teste completo (PowerShell)
```powershell
function Test-TechChallenge {
    Write-Host "🚀 Iniciando testes..." -ForegroundColor Cyan
    
    # 1. Verificar containers
    Write-Host "`n1️⃣  Verificando containers..." -ForegroundColor Yellow
    $containers = docker-compose ps | measure-object | select -ExpandProperty Count
    if ($containers -gt 3) {
        Write-Host "✅ Containers rodando" -ForegroundColor Green
    } else {
        Write-Host "❌ Containers não iniciados" -ForegroundColor Red
        return
    }
    
    # 2. Verificar banco
    Write-Host "`n2️⃣  Verificando banco de dados..." -ForegroundColor Yellow
    $db = docker exec tech-challenge-5-postgres-1 psql -U app -t -c "\l" 2>$null
    if ($db -like "*upload_db*") {
        Write-Host "✅ Banco de dados OK" -ForegroundColor Green
    } else {
        Write-Host "❌ Banco de dados com problema" -ForegroundColor Red
    }
    
    # 3. Testar endpoint
    Write-Host "`n3️⃣  Testando endpoint..." -ForegroundColor Yellow
    try {
        $response = curl.exe -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/upload
        if ($response -eq "405" -or $response -eq "415") {  # 405/415 é esperado pois requer POST com arquivo
            Write-Host "✅ Endpoint acessível (HTTP $response)" -ForegroundColor Green
        } else {
            Write-Host "❌ Endpoint retornou HTTP $response" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Erro ao acessar endpoint" -ForegroundColor Red
    }
    
    Write-Host "`n✅ Teste completo!" -ForegroundColor Green
}

# Usar:
# Test-TechChallenge
```

### Limpeza Rápida

#### Parar tudo
```powershell
docker-compose stop
Write-Host "✅ Serviços parados" -ForegroundColor Green
```

#### Apagar tudo (PERIGOSO!)
```powershell
docker-compose down -v
Write-Host "⚠️  Tudo foi apagado (volumes incluídos)" -ForegroundColor Yellow
```

#### Verificar espaço em disco
```powershell
docker system df
```

---

## 📞 Suporte

Se encontrar erros após refatoração:

1. **Import Error**: Verificar que shared está instalado
2. **Database Connection**: Verificar DATABASE_URL no docker-compose
3. **Celery Tasks**: Verificar que Redis está saudável
4. **File Upload**: Verificar MinIO endpoint e credenciais

### Verificação Rápida (PowerShell)
```powershell
Write-Host "Verificando componentes..." -ForegroundColor Cyan
Write-Host "✓ PostgreSQL: " -NoNewline; (docker ps --format "{{.Names}}" | Select-String "postgres") ? "✅" : "❌"
Write-Host "✓ Redis: " -NoNewline; (docker ps --format "{{.Names}}" | Select-String "redis") ? "✅" : "❌"
Write-Host "✓ MinIO: " -NoNewline; (docker ps --format "{{.Names}}" | Select-String "minio") ? "✅" : "❌"
Write-Host "✓ Upload: " -NoNewline; (docker ps --format "{{.Names}}" | Select-String "upload") ? "✅" : "❌"
Write-Host "✓ Processor: " -NoNewline; (docker ps --format "{{.Names}}" | Select-String "processor") ? "✅" : "❌"
Write-Host "✓ Reports: " -NoNewline; (docker ps --format "{{.Names}}" | Select-String "reports") ? "✅" : "❌"
```
