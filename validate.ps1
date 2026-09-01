<#
.SYNOPSIS
    Script de validação rápida em camadas para desenvolvedores MedQuest (Windows PowerShell).

.PARAMETER Tier
    Nível de validação: 'fast' (commit local, default), 'standard' (push) ou 'full' (PR).

.EXAMPLE
    .\validate.ps1 fast
    .\validate.ps1 standard
    .\validate.ps1 full
#>

param (
    [ValidateSet("fast", "standard", "full")]
    [string]$Tier = "fast"
)

$PythonExe = "python"
if (Test-Path "app\backend\.venv\Scripts\python.exe") {
    $PythonExe = "app\backend\.venv\Scripts\python.exe"
}

& $PythonExe scripts\dev_check.py --tier $Tier
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
