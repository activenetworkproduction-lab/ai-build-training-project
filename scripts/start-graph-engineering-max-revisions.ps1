<#
一键运行 07_graph-engineering 的 MAX_REVISIONS 边界情况演示：用一个永远要求修改的
假评论者，验证环不会无限转下去。不需要 GEMINI_API_KEY，用固定的假函数确定性复现。
用法：powershell -File scripts/start-graph-engineering-max-revisions.ps1
#>
$repoRoot = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    Write-Host "找不到 .venv，请先在仓库根目录运行: python -m venv .venv 然后 .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

$env:PYTHONUTF8 = '1'
& $py (Join-Path $repoRoot '07_graph-engineering\demo_max_revisions.py')

$html = Join-Path $repoRoot '07_graph-engineering\trace_visualization.html'
if (Test-Path $html) {
    Start-Process $html
}
