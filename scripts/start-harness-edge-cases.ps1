<#
一键运行 05_harness 的边界情况演示（失败重试/评估打回重答/权限拒绝）。
不需要 GEMINI_API_KEY，用固定的假函数确定性复现，方便随时跑、方便下断点调试。
用法：powershell -File scripts/start-harness-edge-cases.ps1
#>
$repoRoot = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    Write-Host "找不到 .venv，请先在仓库根目录运行: python -m venv .venv 然后 .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

$env:PYTHONUTF8 = '1'
& $py (Join-Path $repoRoot '05_harness\demo_edge_cases.py')

$html = Join-Path $repoRoot '05_harness\trace_visualization.html'
if (Test-Path $html) {
    Start-Process $html
}
