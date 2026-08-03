# 项目二：用 MCP 让 AI 快速查 Excel 内容（教学项目）

MCP（Model Context Protocol）是 Anthropic 提出的一套标准协议，让 AI 客户端（Claude Desktop、
Claude Code 等）能够统一的方式连接各种外部工具/数据源。这个项目做一个 MCP Server，
让 AI 能够读取、查询本地 Excel 文件的内容。

## 当前状态：已完整实现

- ✅ `src/server.ts`：MCP Server，注册了 4 个工具：
  - `ping`：验证握手用的最小示例
  - `list_sheets`：列出 Excel 文件里有哪些工作表
  - `query_sheet`：读取指定工作表的数据（第一行当表头，返回对象数组）
  - `search_excel`：在所有工作表里搜索关键字，返回命中的行
- ✅ `src/client-demo.ts`：**手写的 MCP 客户端连接演示**（见下方"重点：手写演示"），
  已扩展成依次调用上面 4 个工具，全部用真实 Excel 文件验证跑通
- ✅ `scripts/gen-sample-data.ts`：生成演示用的 `sample-data/company.xlsx`
  （"员工"和"产品"两个工作表）

## 重点：手写演示 MCP 的"引用"过程

平时接入一个 MCP Server，只需要在 Claude Desktop 的配置文件里加几行 JSON：

```json
{
  "mcpServers": {
    "excel-mcp-server": {
      "command": "node",
      "args": ["--experimental-strip-types", "D:/workspace/.../src/server.ts"]
    }
  }
}
```

这几行 JSON 背后，Claude Desktop 帮你做了 4 件事，`src/client-demo.ts` 把这 4 步**手写了一遍**，
让你看清楚配置文件背后到底发生了什么：

1. **描述怎么启动 Server**——就是配置文件里的 `command`/`args`
2. **创建 Client 并 `connect()`**——SDK 在背后拉起 Server 进程，通过它的 stdin/stdout
   完成 MCP 的 `initialize` 握手
3. **`listTools()`**——问服务端"你有哪些工具"，这一步对应 AI 客户端里"发现"某个 MCP 提供了什么能力
4. **`callTool()`**——真正调用工具，拿到结果，这一步对应 AI 决定"我要用这个工具"之后发生的事

`client-demo.ts` 在第 4 步依次调用了 `list_sheets`→`query_sheet`→`search_excel`，
模拟 AI 在对话里"帮你查 Excel"的完整过程。

## 本地运行

```bash
# 首次运行前先生成样例 Excel 文件
pnpm --filter excel-mcp-server gen-sample

# 单独启动 server（用于手动调试，会一直挂起等待 stdin 输入，Ctrl+C 退出）
pnpm --filter excel-mcp-server server

# 运行手写演示：拉起 server 子进程、完成握手、依次调用 4 个工具、打印结果
pnpm --filter excel-mcp-server demo
```

## 接入 Claude Desktop

编辑 Claude Desktop 的配置文件（Windows: `%APPDATA%\Claude\claude_desktop_config.json`），
在 `mcpServers` 里加入本项目的 `server.ts` 路径（参考上面的 JSON 示例，改成你本机的绝对路径），
重启 Claude Desktop 即可在对话里直接让 AI 帮你查 `sample-data/company.xlsx`。

出于安全考虑，三个 Excel 工具都限制只能访问 `sample-data/` 目录下的文件（见
`server.ts` 里的 `resolveSafePath`），不能通过 `fileName` 参数访问任意路径。

## 依赖说明

- `@modelcontextprotocol/sdk`：官方 MCP SDK，`McpServer` 高层封装 + `Client`/`StdioClientTransport`
- `exceljs`：读写 `.xlsx` 文件
- `zod`：给工具参数写 schema，SDK 会自动校验客户端传入的参数
