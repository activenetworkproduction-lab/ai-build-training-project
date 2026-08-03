<#
一键生成 embedding 可视化 demo：把 documents 表里的向量投影到 2 维并生成 HTML，自动用默认浏览器打开。
前提：已运行过 scripts/start-vector-ingest.ps1（documents 表里要有数据）。
用法：powershell -File scripts/start-vector-visualize.ps1
#>
$repoRoot = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    Write-Host "找不到 .venv，请先在仓库根目录运行: python -m venv .venv 然后 .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

$env:PYTHONUTF8 = '1'
& $py (Join-Path $repoRoot '03_vector\visualize_embeddings.py')

$html = Join-Path $repoRoot '03_vector\embeddings_visualization.html'
if (Test-Path $html) {
    Start-Process $html
}
