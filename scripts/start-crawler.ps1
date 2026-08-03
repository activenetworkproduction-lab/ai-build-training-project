<#
一键运行爬虫：抓取中文维基百科上几个 RAG 相关词条，产出到 data/raw/。
用法：powershell -File scripts/start-crawler.ps1
#>
$repoRoot = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    Write-Host "找不到 .venv，请先在仓库根目录运行: python -m venv .venv 然后 .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

$env:PYTHONUTF8 = '1'
& $py (Join-Path $repoRoot '00_crawler\crawl.py')
