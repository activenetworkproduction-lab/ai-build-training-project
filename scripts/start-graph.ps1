<#
一键运行 Agent Graph 样例：研究员 → 写手 → 评论者，评论者可以打回写手重写。
用法：powershell -File scripts/start-graph.ps1
     powershell -File scripts/start-graph.ps1 -Topic "自定义主题"
#>
param(
    [string]$Topic
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    Write-Host "找不到 .venv，请先在仓库根目录运行: python -m venv .venv 然后 .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

$env:PYTHONUTF8 = '1'
if ($Topic) {
    & $py (Join-Path $repoRoot 'agent-engineering\graph\main.py') $Topic
} else {
    & $py (Join-Path $repoRoot 'agent-engineering\graph\main.py')
}
