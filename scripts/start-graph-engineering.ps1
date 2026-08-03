<#
一键运行 Agent Graph 编排样例（07_graph-engineering）：研究员 → 写手 → 评论者，
评论者可以打回写手重写。注意这个"图"是 agent 编排图，不是 04_graph 那个 Neo4j 知识图谱。
用法：powershell -File scripts/start-graph-engineering.ps1
     powershell -File scripts/start-graph-engineering.ps1 -Topic "自定义主题"
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
    & $py (Join-Path $repoRoot '07_graph-engineering\main.py') $Topic
} else {
    & $py (Join-Path $repoRoot '07_graph-engineering\main.py')
}
