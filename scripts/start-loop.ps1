<#
一键运行通用 Agent Loop 样例：计算器 + 汇率转换，模型自己决定要串联几步。
用法：powershell -File scripts/start-loop.ps1
     powershell -File scripts/start-loop.ps1 -Question "自定义问题"
#>
param(
    [string]$Question
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    Write-Host "找不到 .venv，请先在仓库根目录运行: python -m venv .venv 然后 .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

$env:PYTHONUTF8 = '1'
if ($Question) {
    & $py (Join-Path $repoRoot 'agent-engineering\loop\main.py') $Question
} else {
    & $py (Join-Path $repoRoot 'agent-engineering\loop\main.py')
}
