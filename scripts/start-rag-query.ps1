<#
一键运行 RAG 查询：BM25 / 向量 / 图 / Agentic 四选一。
用法（交互式）：powershell -File scripts/start-rag-query.ps1
用法（直接指定）：powershell -File scripts/start-rag-query.ps1 -Mode bm25 -Question "PostgreSQL 扩展"
#>
param(
    [ValidateSet('bm25', 'vector', 'graph', 'agentic')]
    [string]$Mode,
    [string]$Question
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    Write-Host "找不到 .venv，请先在仓库根目录运行: python -m venv .venv 然后 .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

if (-not $Mode) {
    Write-Host "选择查询方式：" -ForegroundColor Cyan
    Write-Host "  1) BM25 关键词查询"
    Write-Host "  2) 向量语义查询"
    Write-Host "  3) 图查询"
    Write-Host "  4) Agentic 多轮查询"
    $choice = Read-Host "输入 1-4"
    $modeMap = @{ '1' = 'bm25'; '2' = 'vector'; '3' = 'graph'; '4' = 'agentic' }
    $Mode = $modeMap[$choice]
    if (-not $Mode) {
        Write-Host "无效选项：$choice" -ForegroundColor Red
        exit 1
    }
}

if (-not $Question) {
    $Question = Read-Host "输入你的问题"
}

$scriptMap = @{
    'bm25'    = 'query_bm25.py'
    'vector'  = 'query_vector.py'
    'graph'   = 'query_graph.py'
    'agentic' = 'query_agentic.py'
}

$env:PYTHONUTF8 = '1'
& $py (Join-Path $repoRoot "rag-query\$($scriptMap[$Mode])") $Question
