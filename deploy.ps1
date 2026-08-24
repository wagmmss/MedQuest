<#
.SYNOPSIS
    Deploy automatizado e de alta performance do MedQuest para o servidor online (VPS).

.DESCRIPTION
    Realiza o fluxo completo e otimizado de deploy:
    1. Detecta quais componentes foram alterados (Backend, Frontend ou ambos)
    2. Realiza git add e git commit com mensagem informativa
    3. Realiza git push para origin main (acionando build ultrarrapido no GitHub Actions)
    4. Conecta via SSH a VPS (136.248.114.130)
    5. Executa git pull origin main no servidor
    6. Atualiza os containers de forma inteligente:
       - Tenta baixar as imagens prontas do GitHub Container Registry (5 a 10 segundos)
       - Fallback: se compilar localmente, executa build seletivo e otimizado sem travar a VPS
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

.PARAMETER SkipGit
    Pula o commit e push local, executando apenas o deploy remoto na VPS.

.PARAMETER SkipRemote
    Pula o deploy remoto, realizando apenas o commit e push local.

.PARAMETER ForceBuild
    Forca o build local na VPS em vez de tentar baixar do GHCR.

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
    [string]$RemoteDir = "~/MedQuest",
    [switch]$SkipGit,
    [switch]$SkipRemote,
    [switch]$ForceBuild
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

# Variaveis para rastreio de escopo
$BackendChanged = $true
$FrontendChanged = $true

# ==============================================================================
# ETAPA 1: GIT LOCAL (Add, Commit, Push)
# ==============================================================================
if (-not $SkipGit) {
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
        # Analise de escopo de mudanca
        $BackendChanged = [bool]($ChangedFiles | Select-String "app/backend")
        $FrontendChanged = [bool]($ChangedFiles | Select-String "app/frontend")

        if ($BackendChanged -and -not $FrontendChanged) {
            Print-Info "Escopo detectado: Apenas Backend (Python/Flask)"
        } elseif ($FrontendChanged -and -not $BackendChanged) {
            Print-Info "Escopo detectado: Apenas Frontend (Next.js/React)"
        } else {
            Print-Info "Escopo detectado: Completo (Backend + Frontend)"
        }

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
# ETAPA 2: DEPLOY REMOTO OTIMIZADO NA VPS
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

    $ForceFlag = if ($ForceBuild) { "true" } else { "false" }
    $OnlyBackend = if ($BackendChanged -and -not $FrontendChanged) { "true" } else { "false" }
    $OnlyFrontend = if ($FrontendChanged -and -not $BackendChanged) { "true" } else { "false" }

    # Script bash que executa na VPS com estrategia de pull rapido ou build seletivo
    $RemoteBashScript = @"
set -e
echo "  [VPS 1/3] Atualizando repositorio..."
cd ~/MedQuest
git pull origin main

echo "  [VPS 2/3] Atualizando containers Docker..."
FORCE_BUILD="$ForceFlag"
ONLY_BACKEND="$OnlyBackend"
ONLY_FRONTEND="$OnlyFrontend"

if [ "\$FORCE_BUILD" != "true" ] && sudo docker-compose pull 2>/dev/null; then
    echo "  -> Imagens pre-compiladas baixadas com sucesso do GitHub Packages!"
    sudo docker-compose up -d --force-recreate
else
    if [ "\$ONLY_BACKEND" = "true" ]; then
        echo "  -> Build rapido seletivo: Backend apenas (~5s)..."
        sudo docker-compose up -d --build --force-recreate backend
    elif [ "\$ONLY_FRONTEND" = "true" ]; then
        echo "  -> Build rapido seletivo: Frontend apenas..."
        sudo docker-compose up -d --build --force-recreate frontend
    else
        echo "  -> Build completo com otimizacoes..."
        sudo docker-compose up -d --build --force-recreate
    fi
fi

echo "  [VPS 3/3] Limpando imagens antigas..."
sudo docker image prune -f > /dev/null 2>&1 || true

echo ""
echo "  Status atual dos servicos:"
sudo docker-compose ps
"@

    $SshArgs += "$RemoteBashScript"

    Print-Info "Executando atualizacao dos servicos na VPS..."
    & ssh @SshArgs

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
