<#
一键启动 OCR 项目：后端 (NestJS) + 前端 (Vite)，各开一个新窗口方便看日志。
用法：powershell -File scripts/start-ocr.ps1
#>
$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "启动 OCR 后端 http://localhost:3040 和前端 http://localhost:5102（各开一个新窗口）…" -ForegroundColor Cyan
Start-Process powershell -ArgumentList '-NoExit', '-Command', "cd '$repoRoot'; pnpm dev:ocr:server"
Start-Process powershell -ArgumentList '-NoExit', '-Command', "cd '$repoRoot'; pnpm dev:ocr:web"
Write-Host "已在新窗口启动，关闭对应窗口或 Ctrl+C 即可停止。"
