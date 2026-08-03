<#
一键运行 Agent Harness 样例：工具注册/上下文/权限/状态/恢复/评估六大组件演示。
用法：powershell -File scripts/start-harness.ps1
     powershell -File scripts/start-harness.ps1 -Question "自定义问题"
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
    & $py (Join-Path $repoRoot '05_harness\main.py') $Question
} else {
    & $py (Join-Path $repoRoot '05_harness\main.py')
}
