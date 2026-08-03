<#
一键运行向量入库：把 data/raw/*.txt 分段、生成 embedding，写入 Postgres 的 documents 表。
前提：已运行过 scripts/start-crawler.ps1，且 common/embedding.py 里的 embed_text 已实现。
用法：powershell -File scripts/start-vector-ingest.ps1
#>
$repoRoot = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    Write-Host "找不到 .venv，请先在仓库根目录运行: python -m venv .venv 然后 .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

$env:PYTHONUTF8 = '1'
& $py (Join-Path $repoRoot 'data-pipeline\vector-ingest\ingest.py')
