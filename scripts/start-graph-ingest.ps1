<#
一键运行图谱入库：把 data/raw/*.txt 逐句拆成三元组，写入 Neo4j。
前提：已运行过 scripts/start-crawler.ps1，且 common/extraction.py 里的 extract_triples 已实现。
用法：powershell -File scripts/start-graph-ingest.ps1
#>
$repoRoot = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    Write-Host "找不到 .venv，请先在仓库根目录运行: python -m venv .venv 然后 .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

$env:PYTHONUTF8 = '1'
& $py (Join-Path $repoRoot '04_graph\ingest.py')
