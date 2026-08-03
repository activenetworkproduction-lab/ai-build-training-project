<#
一键环境搭建脚本（面向"刚从 GitHub 拉下代码"的全新环境）：
  1. 检测/安装 Docker，启动 Postgres(pgvector) + Neo4j + pgAdmin 三个容器，
     等 Postgres 就绪（建库建表的 SQL 在容器首次启动时自动跑过，见 docker/postgres-init/01-init.sql）
  2. 检测/安装 Node.js + pnpm，跑 pnpm install（01_ai-ocr 用）
  3. 检测 Python，建 .venv 虚拟环境，跑 pip install -r requirements.txt
     （00/02/03/04/05/06/07 这些 Python 项目共用这一个虚拟环境）
  4. 复制 .env.example 为 .env（如果还没有的话，不会覆盖已有配置）
  5. 打印各个管理界面的访问地址和账号密码，以及后续要做的事

用法：
  powershell -File scripts/setup.ps1
#>

# 注意：不设 $ErrorActionPreference = 'Stop' —— 部分命令偶尔会往 stderr 打无害的
# WARNING（比如 docker 的 WSL2 后端提示），设成 Stop 会把这类 warning 也提升成终止性错误。
# 本脚本改用显式检查 $LASTEXITCODE 的方式判断每一步是否成功。
$repoRoot = Split-Path -Parent $PSScriptRoot

function Test-Command($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

# ============================================================
# 第 1 部分：Docker + 数据库容器
# ============================================================

Write-Host "== 第 1 步：检测 Docker ==" -ForegroundColor Cyan
if (-not (Test-Command 'docker')) {
    Write-Host "未检测到 docker 命令，尝试用 winget 安装 Docker Desktop…" -ForegroundColor Yellow
    if (-not (Test-Command 'winget')) {
        Write-Host "本机也没有 winget，无法自动安装。请手动安装 Docker Desktop：https://www.docker.com/products/docker-desktop/" -ForegroundColor Red
        exit 1
    }
    winget install -e --id Docker.DockerDesktop
    Write-Host "Docker Desktop 安装完成，请手动启动一次 Docker Desktop（可能需要重新登录 Windows），" -ForegroundColor Yellow
    Write-Host "启动完成后重新运行本脚本。" -ForegroundColor Yellow
    exit 0
}
Write-Host "已安装：$(docker --version)"

Write-Host "`n== 第 2 步：检测 Docker 是否正在运行 ==" -ForegroundColor Cyan
# 注意：docker info 用 2>&1 合并 stderr 会导致 PowerShell 5.1 把每行 stderr 包成
# NativeCommandError，进而让 $? 变 false（哪怕退出码其实是 0），所以这里不合并 stderr，
# 只看 $LASTEXITCODE。
docker info *>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker 已安装但没有运行，请先启动 Docker Desktop，再重新运行本脚本。" -ForegroundColor Red
    exit 1
}
Write-Host "Docker 正在运行"

Write-Host "`n== 第 3 步：启动容器（Postgres + pgvector / Neo4j / pgAdmin）==" -ForegroundColor Cyan
Push-Location (Join-Path $repoRoot 'docker')
try {
    docker compose up -d
    if ($LASTEXITCODE -ne 0) { throw "docker compose up 失败" }
}
finally {
    Pop-Location
}

Write-Host "`n== 第 4 步：等待 Postgres 就绪 ==" -ForegroundColor Cyan
$pgReady = $false
for ($i = 0; $i -lt 30; $i++) {
    docker exec training-postgres pg_isready -U rag *>$null
    if ($LASTEXITCODE -eq 0) { $pgReady = $true; break }
    Start-Sleep -Seconds 2
}
if ($pgReady) {
    Write-Host "Postgres 已就绪，vector 扩展和 documents 表已在首次启动时自动创建" -ForegroundColor Green
}
else {
    Write-Host "等待 Postgres 就绪超时，稍后可以手动运行: docker logs training-postgres" -ForegroundColor Yellow
}

# ============================================================
# 第 2 部分：Node.js + pnpm（01_ai-ocr 用）
# ============================================================

Write-Host "`n== 第 5 步：检测 Node.js / pnpm ==" -ForegroundColor Cyan
if (-not (Test-Command 'node')) {
    Write-Host "未检测到 node 命令，尝试用 winget 安装 Node.js LTS…" -ForegroundColor Yellow
    if (-not (Test-Command 'winget')) {
        Write-Host "本机也没有 winget，无法自动安装。请手动安装 Node.js：https://nodejs.org/" -ForegroundColor Red
        exit 1
    }
    winget install -e --id OpenJS.NodeJS.LTS
    Write-Host "Node.js 安装完成，请重新打开一个终端（让 PATH 生效）后再运行本脚本。" -ForegroundColor Yellow
    exit 0
}
Write-Host "已安装：node $(node --version)"

if (-not (Test-Command 'pnpm')) {
    Write-Host "未检测到 pnpm，尝试用 corepack 启用（Node 自带）…" -ForegroundColor Yellow
    corepack enable *>$null
    corepack prepare pnpm@latest --activate *>$null
    if (-not (Test-Command 'pnpm')) {
        Write-Host "corepack 方式失败，改用 npm 全局安装 pnpm…" -ForegroundColor Yellow
        npm install -g pnpm *>$null
    }
    if (-not (Test-Command 'pnpm')) {
        Write-Host "pnpm 安装失败，请手动安装：npm install -g pnpm" -ForegroundColor Red
        exit 1
    }
}
Write-Host "已安装：pnpm $(pnpm --version)"

Write-Host "`n== 第 6 步：pnpm install（01_ai-ocr）==" -ForegroundColor Cyan
Push-Location $repoRoot
try {
    pnpm install
    if ($LASTEXITCODE -ne 0) { throw "pnpm install 失败" }
}
finally {
    Pop-Location
}

# ============================================================
# 第 3 部分：Python 虚拟环境（00/02/03/04/05/06/07 共用）
# ============================================================

Write-Host "`n== 第 7 步：检测 Python ==" -ForegroundColor Cyan
$pythonCmd = $null
foreach ($candidate in @('python', 'py')) {
    if (Test-Command $candidate) { $pythonCmd = $candidate; break }
}
if (-not $pythonCmd) {
    Write-Host "未检测到 python/py 命令，尝试用 winget 安装 Python…" -ForegroundColor Yellow
    if (-not (Test-Command 'winget')) {
        Write-Host "本机也没有 winget，无法自动安装。请手动安装 Python 3.11+：https://www.python.org/downloads/" -ForegroundColor Red
        exit 1
    }
    winget install -e --id Python.Python.3.12
    Write-Host "Python 安装完成，请重新打开一个终端（让 PATH 生效）后再运行本脚本。" -ForegroundColor Yellow
    exit 0
}
Write-Host "已安装：$(& $pythonCmd --version)"

Write-Host "`n== 第 8 步：建 Python 虚拟环境 + 装依赖 ==" -ForegroundColor Cyan
$venvPath = Join-Path $repoRoot '.venv'
$venvPython = Join-Path $venvPath 'Scripts\python.exe'

if (-not (Test-Path $venvPython)) {
    Write-Host "创建虚拟环境 .venv…"
    & $pythonCmd -m venv $venvPath
    if (-not (Test-Path $venvPython)) { throw "创建 .venv 失败" }
}
else {
    Write-Host "已存在 .venv，跳过创建"
}

Write-Host "安装 Python 依赖（requirements.txt）…"
& $venvPython -m pip install -q --upgrade pip
& $venvPython -m pip install -q -r (Join-Path $repoRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw "pip install 失败" }
Write-Host "Python 依赖安装完成" -ForegroundColor Green

Write-Host "`n== 第 9 步：准备 .env ==" -ForegroundColor Cyan
$envPath = Join-Path $repoRoot '.env'
$envExamplePath = Join-Path $repoRoot '.env.example'
if (-not (Test-Path $envPath)) {
    Copy-Item $envExamplePath $envPath
    Write-Host "已从 .env.example 创建 .env，记得去填 GEMINI_API_KEY（或 OPENAI_API_KEY）" -ForegroundColor Yellow
}
else {
    Write-Host ".env 已存在，不覆盖"
}

# ============================================================
# 完成
# ============================================================

Write-Host "`n== 全部完成 ==" -ForegroundColor Green
Write-Host "Postgres      : localhost:5532  (用户 rag / 密码 rag_password / 数据库 ragdb)"
Write-Host "Neo4j Browser : http://localhost:7475  (账号 neo4j / 密码 raggraph123)"
Write-Host "pgAdmin       : http://localhost:5050  (登录邮箱 admin@training-project.com / 密码 admin123)"
Write-Host "                打开后左侧已经预置了 Postgres 连接，第一次点开时输入密码 rag_password 即可"
Write-Host ""
Write-Host "下一步：" -ForegroundColor Cyan
Write-Host "  1. 编辑 .env，填入 GEMINI_API_KEY（或 OPENAI_API_KEY）"
Write-Host "  2. powershell -File scripts/start-crawler.ps1        # 抓取教学语料"
Write-Host "  3. powershell -File scripts/start-ocr.ps1            # 或直接玩 OCR 项目"
