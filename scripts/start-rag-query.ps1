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

# 四种查询方式分散在三个不同的编号项目里：
# BM25/向量查询在 03_vector（和"数据怎么切块存向量"放一起），
# 图查询在 04_graph（和"数据怎么切块存图谱"放一起），
# Agentic 查询单独是 02_ai-rag（它调用的正是 03/04 里这几个查询函数）
$scriptMap = @{
    'bm25'    = '03_vector\query_bm25.py'
    'vector'  = '03_vector\query_vector.py'
    'graph'   = '04_graph\query_graph.py'
    'agentic' = '02_ai-rag\query_agentic.py'
}

$env:PYTHONUTF8 = '1'
& $py (Join-Path $repoRoot $scriptMap[$Mode]) $Question
