<#
一键运行 06_loop 的工具报错边界情况演示：模型先用了不支持的币种触发工具报错，
再换成支持的币种重试。不需要 GEMINI_API_KEY，用固定的假函数确定性复现。
用法：powershell -File scripts/start-loop-tool-error.ps1
#>
$repoRoot = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    Write-Host "找不到 .venv，请先在仓库根目录运行: python -m venv .venv 然后 .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

$env:PYTHONUTF8 = '1'
& $py (Join-Path $repoRoot '06_loop\demo_tool_error.py')

$html = Join-Path $repoRoot '06_loop\trace_visualization.html'
if (Test-Path $html) {
    Start-Process $html
}
