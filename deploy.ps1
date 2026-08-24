<#
.SYNOPSIS
    Deploy automatizado do MedQuest para o servidor online (VPS).

.DESCRIPTION
    Realiza o fluxo completo de deploy:
    1. Verifica alteracoes locais no Git
    2. Realiza git add e git commit (com mensagem informada ou gerada automaticamente)
    3. Realiza git push para origin main
    4. Conecta via SSH a VPS (136.248.114.130) usando sua-chave.key
    5. Executa git pull origin main no servidor
    6. Reconstroi e reinicia os containers Docker (sudo docker-compose up -d --build)
    7. Limpa imagens Docker nao utilizadas (prune)
    8. Exibe o status final dos servicos

.PARAMETER Message
    Mensagem do commit. Se nao fornecida e houver alteracoes, sera solicitada ou gerada com timestamp.

.PARAMETER HostName
    IP ou dominio do servidor VPS (Padrao: 136.248.114.130).

.PARAMETER User
    Usuario SSH do servidor (Padrao: ubuntu).

.PARAMETER KeyFile
    Caminho para o arquivo de chave SSH (.key/.pem/id_rsa). Padrao: sua-chave.key no diretorio do projeto.

.PARAMETER RemoteDir
    Diretorio do projeto no servidor remoto (Padrao: ~/MedQuest).

.PARAMETER SkipGit
    Pula o commit e push local, executando apenas o deploy remoto.

.PARAMETER SkipRemote
    Pula a execucao remota na VPS, realizando apenas o commit e push local.

.EXAMPLE
    .\deploy.ps1
    .\deploy.ps1 "Correcao de layout no dashboard"
    .\deploy.ps1 -SkipGit
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
    [switch]$SkipRemote
)

$ErrorActionPreference = "Stop"
$StartTime = Get-Date

function Print-Header {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "             MEDQUEST - DEPLOY AUTOMATIZADO                 " -ForegroundColor Cyan
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
    Print-Step "1/3" "Processando alteracoes no repositorio local (Git)"

    $GitCmd = Get-Command "git" -ErrorAction SilentlyContinue
    if (-not $GitCmd) {
        Print-Error "Git nao foi encontrado no PATH do sistema."
        exit 1
    }

    # Verificar status do repositorio
    $GitStatus = git status --porcelain
    $HasChanges = [bool]($GitStatus -and $GitStatus.Trim().Length -gt 0)

    if ($HasChanges) {
        Print-Info "Alteracoes detectadas no codigo local."

        # Definir mensagem de commit se nao foi informada via parametro
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
        
        # Git Add
        git add -A
        if ($LASTEXITCODE -ne 0) {
            Print-Error "Falha ao adicionar arquivos com 'git add -A'."
            exit $LASTEXITCODE
        }
        Print-Success "Arquivos adicionados para commit."

        # Git Commit
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
    Print-Info "Enviando commits para o repositorio remoto (origin main)..."
    git push origin main
    if ($LASTEXITCODE -ne 0) {
        Print-Error "Falha ao enviar alteracoes para o GitHub ('git push origin main')."
        Print-Info "Verifique se ha conflitos ou se sua conexao com a internet esta ativa."
        exit $LASTEXITCODE
    }
    Print-Success "Codigo enviado com sucesso para o GitHub."
} else {
    Print-Info "Etapa Git local pulada conforme solicitado (-SkipGit)."
}

# ==============================================================================
# ETAPA 2: DEPLOY REMOTO VIA SSH
# ==============================================================================
if (-not $SkipRemote) {
    Print-Step "2/3" "Conectando ao servidor e atualizando servicos ($User@$HostName)"

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

    $RemoteBashScript = @'
set -e
echo "  [VPS 1/4] Atualizando codigo do MedQuest via Git..."
cd ~/MedQuest
git pull origin main

echo "  [VPS 2/4] Reconstruindo e subindo containers Docker..."
sudo docker-compose up -d --build --force-recreate

echo "  [VPS 3/4] Limpando imagens Docker antigas..."
sudo docker image prune -f > /dev/null 2>&1 || true

echo "  [VPS 4/4] Status atual dos servicos:"
sudo docker-compose ps
'@

    $SshArgs += "$RemoteBashScript"

    Print-Info "Executando rebuild e deploy na VPS..."
    & ssh @SshArgs

    if ($LASTEXITCODE -ne 0) {
        Print-Error "Ocorreu um erro durante a execucao do deploy remoto via SSH (Exit code: $LASTEXITCODE)."
        exit $LASTEXITCODE
    }
    Print-Success "Deploy remoto concluido no servidor!"
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
