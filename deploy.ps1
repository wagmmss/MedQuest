<#
.SYNOPSIS
    Deploy automatizado e de alta performance do MedQuest para o servidor online (VPS).

.DESCRIPTION
    Realiza o fluxo completo e otimizado de deploy:
    1. Verifica alteracoes locais no Git
    2. Realiza git add e git commit com mensagem informativa
    3. Realiza git push para origin main (acionando build ultrarrapido no GitHub Actions)
    4. Conecta via SSH a VPS (136.248.114.130)
    5. Executa git pull origin main no servidor
    6. Atualiza os containers:
       - Baixa em paralelo as imagens prontas do GitHub Container Registry
    7. Limpa imagens Docker nao utilizadas (prune)
    8. Exibe o status final dos servicos

.PARAMETER Message
    Mensagem do commit. Se nao fornecida, sera solicitada ou gerada com timestamp.

.PARAMETER HostName
    IP ou dominio da VPS (Padrao: 136.248.114.130).

.PARAMETER User
    Usuario SSH (Padrao: ubuntu).

.PARAMETER KeyFile
    Caminho da chave SSH (Padrao: sua-chave.key no diretorio do projeto).

.PARAMETER RemoteDir
    Diretorio do projeto no servidor remoto (Padrao: /home/ubuntu/MedQuest).

.PARAMETER ImageWaitSeconds
    Tempo maximo, em segundos, para aguardar as imagens do commit serem publicadas
    pelo GitHub Actions (Padrao: 600).

.PARAMETER SkipGit
    Pula o commit e push local, executando apenas o deploy remoto na VPS.

.PARAMETER SkipRemote
    Pula o deploy remoto, realizando apenas o commit e push local.

.EXAMPLE
    deploy
    deploy "Ajustes no planner"
    deploy -SkipGit
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Message,

    [string]$HostName = "136.248.114.130",
    [string]$User = "ubuntu",
    [string]$KeyFile = "",
    [string]$RemoteDir = "/home/ubuntu/MedQuest",
    [ValidateRange(15, 3600)]
    [int]$ImageWaitSeconds = 600,
    [switch]$SkipGit,
    [switch]$SkipRemote
)

$ErrorActionPreference = "Stop"
$StartTime = Get-Date

function Print-Header {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "         MEDQUEST - DEPLOY AUTOMATIZADO DE ALTA VELOCIDADE   " -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Print-Step {
    param([string]$Step, [string]$Title)
    Write-Host ""
    Write-Host "[$Step] $Title" -ForegroundColor Yellow
    Write-Host ("-" * (4 + $Step.Length + $Title.Length)) -ForegroundColor DarkGray
}

function Print-Success {
    param([string]$Text)
    Write-Host "  [OK] $Text" -ForegroundColor Green
}

function Print-Info {
    param([string]$Text)
    Write-Host "  [i]  $Text" -ForegroundColor Gray
}

function Print-Error {
    param([string]$Text)
    Write-Host "  [ERRO] $Text" -ForegroundColor Red
}

Print-Header

# 1. Resolver diretorio raiz do projeto
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = (Get-Location).Path
}
Set-Location $ProjectRoot

# 2. Localizar chave SSH
if (-not $KeyFile) {
    $CandidateKey = Join-Path $ProjectRoot "sua-chave.key"
    if (Test-Path $CandidateKey) {
        $KeyFile = $CandidateKey
    } else {
        $DefaultSSHKey = Join-Path $env:USERPROFILE ".ssh\id_rsa"
        if (Test-Path $DefaultSSHKey) {
            $KeyFile = $DefaultSSHKey
        }
    }
}

# Validacao do SSH local
$SshCmd = Get-Command "ssh" -ErrorAction SilentlyContinue
if (-not $SshCmd) {
    Print-Error "Cliente OpenSSH ('ssh') nao foi encontrado no PATH do sistema."
    exit 1
}

# ==============================================================================
# ETAPA 1: GIT LOCAL (Add, Commit, Push)
# ==============================================================================
if (-not $SkipGit) {
    # 0. Sincronizar automaticamente novas questões com o Turso Cloud se houver
    $SyncScript = Join-Path $ProjectRoot "app\backend\scripts\sync_incremental_turso.py"
    if (Test-Path $SyncScript) {
        Print-Step "0/3" "Sincronizando banco de dados com Turso Cloud"
        uv run --with requests --with python-dotenv python $SyncScript
        if ($LASTEXITCODE -eq 0) {
            Print-Success "Turso Cloud em sincronia com banco local."
        } else {
            Print-Info "Aviso: Sincronizacao com Turso ignorada ou falhou, prosseguindo com deploy."
        }
    }

    Print-Step "1/3" "Processando alteracoes locais no Git"

    $GitCmd = Get-Command "git" -ErrorAction SilentlyContinue
    if (-not $GitCmd) {
        Print-Error "Git nao foi encontrado no PATH do sistema."
        exit 1
    }

    # Analisar arquivos alterados
    $ChangedFiles = git status --porcelain
    $HasChanges = [bool]($ChangedFiles -and $ChangedFiles.Trim().Length -gt 0)

    if ($HasChanges) {
        # Definir mensagem de commit se nao fornecida
        if (-not $Message) {
            $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
            if ([Environment]::UserInteractive -and -not [Console]::IsInputRedirected) {
                Write-Host ""
                $UserMsg = Read-Host "  Digite a mensagem do commit (Enter para '[deploy] $Timestamp')"
                if ($UserMsg -and $UserMsg.Trim().Length -gt 0) {
                    $Message = $UserMsg.Trim()
                } else {
                    $Message = "[deploy] Atualizacao $Timestamp"
                }
            } else {
                $Message = "[deploy] Atualizacao $Timestamp"
            }
        }

        Print-Info "Mensagem de commit: '$Message'"
        
        git add -A
        if ($LASTEXITCODE -ne 0) {
            Print-Error "Falha ao adicionar arquivos com 'git add -A'."
            exit $LASTEXITCODE
        }

        git commit -m "$Message"
        if ($LASTEXITCODE -ne 0) {
            Print-Error "Falha ao realizar 'git commit'."
            exit $LASTEXITCODE
        }
        Print-Success "Commit realizado com sucesso."
    } else {
        Print-Info "Nenhuma alteracao pendente de commit local."
    }

    # Git Push
    Print-Info "Enviando alteracoes para o GitHub (origin main)..."
    git push origin main
    if ($LASTEXITCODE -ne 0) {
        Print-Error "Falha ao enviar alteracoes para o GitHub ('git push origin main')."
        exit $LASTEXITCODE
    }
    Print-Success "Codigo enviado com sucesso para o GitHub."
} else {
    Print-Info "Etapa Git local pulada conforme solicitado (-SkipGit)."
}

# ==============================================================================
# ETAPA 2: DEPLOY REMOTO NA VPS
# ==============================================================================
if (-not $SkipRemote) {
    Print-Step "2/3" "Atualizando servicos na VPS ($User@$HostName)"

    $SshArgs = @()
    $SshArgs += "-o"
    $SshArgs += "StrictHostKeyChecking=accept-new"
    $SshArgs += "-o"
    $SshArgs += "ConnectTimeout=15"

    if ($KeyFile -and (Test-Path $KeyFile)) {
        Print-Info "Utilizando chave SSH: $KeyFile"
        $SshArgs += "-i"
        $SshArgs += "$KeyFile"
    } else {
        Print-Info "Utilizando autenticacao padrao do SSH/Agent."
    }

    $Target = "$User@$HostName"
    $SshArgs += "$Target"

    # Envia o script pela entrada padrao para o bash remoto. Passar um bloco
    # multilinha como argumento do ssh deixa o quoting a cargo de dois shells
    # (PowerShell e sh) e pode fazer o docker-compose receber argumentos errados.
    #
    # Estrategia: baixar imagens prontas do GHCR (compiladas pelo GitHub Actions)
    # e so recriar containers, sem compilar nada localmente na VPS.
    $RemoteBashScript = @'
set -euo pipefail

PROJ="${1:?Diretorio remoto nao informado}"
IMAGE_WAIT_SECONDS="${2:?Tempo de espera nao informado}"
COMPOSE_FILE="$PROJ/docker-compose.yml"

if ! command -v docker-compose >/dev/null 2>&1; then
    echo "[ERRO] docker-compose nao foi encontrado na VPS." >&2
    exit 1
fi

compose() {
    sudo docker-compose -f "$COMPOSE_FILE" "$@"
}

pull_commit_image() {
    local image="$1"
    local label="$2"
    local deadline=$((SECONDS + IMAGE_WAIT_SECONDS))

    echo "    [$label] Verificando disponibilidade no GitHub Container Registry..."
    while ! sudo docker pull "$image" >/dev/null 2>&1; do
        if (( SECONDS >= deadline )); then
            echo "[ERRO] A imagem $label ($image) nao foi publicada em ${IMAGE_WAIT_SECONDS}s." >&2
            exit 1
        fi

        echo "    [$label] Compilando no GitHub Actions... (${SECONDS}s decorridos)"
        sleep 8
    done
    echo "    [$label] Imagem pronta e baixada com sucesso!"
}

echo "  [VPS 1/4] Atualizando repositorio..."
cd "$PROJ"
git pull --ff-only origin main
DEPLOY_SHA=$(git rev-parse HEAD)
BACKEND_IMAGE="ghcr.io/wagmmss/medquest-backend:sha-$DEPLOY_SHA"
FRONTEND_IMAGE="ghcr.io/wagmmss/medquest-frontend:sha-$DEPLOY_SHA"

echo "  [VPS 2/4] Aguardando e baixando imagens Docker em paralelo do commit $DEPLOY_SHA..."
pull_commit_image "$BACKEND_IMAGE" "Backend" &
backend_pull_pid=$!
pull_commit_image "$FRONTEND_IMAGE" "Frontend" &
frontend_pull_pid=$!

pull_failed=0
wait "$backend_pull_pid" || pull_failed=1
wait "$frontend_pull_pid" || pull_failed=1
if (( pull_failed != 0 )); then
    echo "[ERRO] Nao foi possivel baixar todas as imagens deste deploy." >&2
    exit 1
fi

# O arquivo Compose referencia :latest. Atualizamos essa tag local somente apos
# baixar as imagens imutaveis deste commit, para o Compose recriar com a versao certa.
sudo docker tag "$BACKEND_IMAGE" ghcr.io/wagmmss/medquest-backend:latest
sudo docker tag "$FRONTEND_IMAGE" ghcr.io/wagmmss/medquest-frontend:latest

echo "  [VPS 3/4] Recriando containers com as novas imagens..."
# O Compose compara a imagem/configuracao desejada com cada container existente.
# Sem --force-recreate, servicos inalterados permanecem no ar e somente o que
# realmente mudou e reiniciado.
compose up -d --no-build --remove-orphans

# Mantem somente a tag :latest local. As tags sha-* sao usadas para garantir que
# a imagem correta foi baixada e, em seguida, removidas para o prune liberar as
# imagens de versoes antigas em deploys futuros.
sudo docker image rm "$BACKEND_IMAGE" "$FRONTEND_IMAGE" >/dev/null

echo "  [VPS 4/4] Limpando imagens antigas..."
sudo docker image prune -f > /dev/null 2>&1 || true

echo ""
echo "  Status atual dos servicos:"
compose ps
'@

    Print-Info "Executando atualizacao dos servicos na VPS..."
    # O PowerShell pode acrescentar CR ao fim da entrada redirecionada. O `tr`
    # remove esses caracteres antes de o Bash interpretar o script (por exemplo,
    # impede que o ultimo comando seja lido como `ps\r`).
    $RemoteBashScript | & ssh @SshArgs "tr -d '\r' | bash -s -- '$RemoteDir' $ImageWaitSeconds"

    if ($LASTEXITCODE -ne 0) {
        Print-Error "Ocorreu um erro durante a execucao do deploy remoto via SSH (Exit code: $LASTEXITCODE)."
        exit $LASTEXITCODE
    }
    Print-Success "Servicos atualizados com sucesso na VPS!"
} else {
    Print-Info "Etapa de deploy remoto pulada conforme solicitado (-SkipRemote)."
}

# ==============================================================================
# ETAPA 3: RESUMO E CONCLUSAO
# ==============================================================================
Print-Step "3/3" "Finalizacao"

$Elapsed = (Get-Date) - $StartTime
$Minutes = [int]$Elapsed.TotalMinutes
$Seconds = $Elapsed.Seconds

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "              DEPLOY CONCLUIDO COM SUCESSO!                 " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Print-Success "Tempo total de execucao: ${Minutes}m ${Seconds}s"
Print-Success "MedQuest esta online e atualizado no servidor ($HostName)."
Write-Host ""
