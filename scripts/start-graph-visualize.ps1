<#
一键生成图谱可视化 demo：把 Neo4j 里的实体关系导出成一张力导向节点图 HTML，自动用默认浏览器打开。
前提：已运行过 scripts/start-graph-ingest.ps1（图谱里要有数据）。
用法：powershell -File scripts/start-graph-visualize.ps1
#>
$repoRoot = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    Write-Host "找不到 .venv，请先在仓库根目录运行: python -m venv .venv 然后 .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

$env:PYTHONUTF8 = '1'
& $py (Join-Path $repoRoot '04_graph\visualize_graph.py')

$html = Join-Path $repoRoot '04_graph\graph_visualization.html'
if (Test-Path $html) {
    Start-Process $html
}
