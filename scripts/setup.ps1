<#
一键环境搭建脚本：
  1. 检测本机是否已装 Docker，没有就尝试用 winget 安装（需要手动重启一次电脑/重新登录）
  2. 用 docker/docker-compose.yml 启动 Postgres(pgvector) + Neo4j + pgAdmin 三个容器
  3. 等 Postgres 就绪（建库建表的 SQL 在容器首次启动时已经自动跑过，见 docker/postgres-init/01-init.sql）
  4. 打印各个管理界面的访问地址和账号密码

用法：
  powershell -File scripts/setup.ps1
#>

# 注意：不设 $ErrorActionPreference = 'Stop' —— Docker 命令偶尔会往 stderr 打无害的
# WARNING（比如 WSL2 后端的 blkio 提示），设成 Stop 会把这类 warning 也提升成终止性错误。
# 本脚本改用显式检查 $LASTEXITCODE 的方式判断每一步是否成功。
$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "== 第 1 步：检测 Docker ==" -ForegroundColor Cyan
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Host "未检测到 docker 命令，尝试用 winget 安装 Docker Desktop…" -ForegroundColor Yellow
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        Write-Host "本机也没有 winget，无法自动安装。请手动安装 Docker Desktop：https://www.docker.com/products/docker-desktop/" -ForegroundColor Red
        exit 1
    }
    winget install -e --id Docker.DockerDesktop
    Write-Host "Docker Desktop 安装完成，请手动启动一次 Docker Desktop（可能需要重新登录 Windows），" -ForegroundColor Yellow
    Write-Host "启动完成后重新运行本脚本。" -ForegroundColor Yellow
    exit 0
}
else {
    $version = docker --version
    Write-Host "已安装：$version"
}

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
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    docker exec training-postgres pg_isready -U rag *>$null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    Start-Sleep -Seconds 2
}
if ($ready) {
    Write-Host "Postgres 已就绪，vector 扩展和 documents 表已在首次启动时自动创建" -ForegroundColor Green
}
else {
    Write-Host "等待 Postgres 就绪超时，稍后可以手动运行: docker logs training-postgres" -ForegroundColor Yellow
}

Write-Host "`n== 完成 ==" -ForegroundColor Green
Write-Host "Postgres      : localhost:5532  (用户 rag / 密码 rag_password / 数据库 ragdb)"
Write-Host "Neo4j Browser : http://localhost:7475  (账号 neo4j / 密码 raggraph123)"
Write-Host "pgAdmin       : http://localhost:5050  (登录邮箱 admin@training-project.com / 密码 admin123)"
Write-Host "                打开后左侧已经预置了 Postgres 连接，第一次点开时输入密码 rag_password 即可"
