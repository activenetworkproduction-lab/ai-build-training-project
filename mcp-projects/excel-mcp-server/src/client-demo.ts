import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

/**
 * 【手写演示】这个脚本演示 MCP 客户端"引用/连接"一个 MCP Server 的完整过程 ——
 * 平时我们都是在 Claude Desktop 的配置文件里加几行 JSON 就把这一步"隐藏"掉了，
 * 这里手写出来，是为了看清楚配置文件背后到底发生了什么。
 *
 * 一共 4 步，对应下面代码的 4 段：
 *   1. 描述"怎么启动这个 MCP Server"（命令 + 参数）—— 这就是 Claude Desktop
 *      配置文件里 mcpServers.xxx.command/args 两个字段的来源
 *   2. 创建 Client，调用 connect()：SDK 会在背后启动第 1 步描述的进程，
 *      并通过它的 stdin/stdout 完成 MCP 的 initialize 握手
 *   3. 调用 listTools()：问服务端"你有哪些工具可以用"
 *   4. 调用 callTool()：真正调用其中的工具，拿到结果
 *
 * 运行前先执行一次 `pnpm gen-sample` 生成 sample-data/company.xlsx。
 */
async function main() {
  const serverEntry = path.join(path.dirname(fileURLToPath(import.meta.url)), 'server.ts');

  // ---- 第 1 步：描述如何启动 MCP Server ----
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: ['--experimental-strip-types', '--disable-warning=ExperimentalWarning', serverEntry],
  });

  // ---- 第 2 步：创建客户端并连接（这一步会真正拉起服务端进程 + 完成协议握手）----
  const client = new Client({ name: 'excel-mcp-demo-client', version: '0.0.1' });
  console.log('[demo] 正在连接 MCP Server…');
  await client.connect(transport);
  console.log('[demo] 连接成功，握手完成');

  // ---- 第 3 步：查询服务端提供了哪些工具 ----
  const { tools } = await client.listTools();
  console.log(
    '[demo] 服务端提供的工具列表：',
    tools.map((t) => t.name),
  );

  // ---- 第 4 步：依次调用几个工具，模拟 AI 在对话里"帮你查 Excel"的过程 ----
  console.log('\n[demo] 调用 list_sheets（这个 Excel 文件里有哪些工作表？）');
  const sheets = await client.callTool({
    name: 'list_sheets',
    arguments: { fileName: 'company.xlsx' },
  });
  console.log(firstText(sheets.content));

  console.log('\n[demo] 调用 query_sheet（把"员工"工作表的内容读出来）');
  const rows = await client.callTool({
    name: 'query_sheet',
    arguments: { fileName: 'company.xlsx', sheetName: '员工' },
  });
  console.log(firstText(rows.content));

  console.log('\n[demo] 调用 search_excel（搜索关键字"技术部"）');
  const matches = await client.callTool({
    name: 'search_excel',
    arguments: { fileName: 'company.xlsx', keyword: '技术部' },
  });
  console.log(firstText(matches.content));

  await client.close();
  console.log('\n[demo] 已断开连接');
}

function firstText(content: unknown): string {
  if (Array.isArray(content) && content[0]?.type === 'text') {
    return content[0].text as string;
  }
  return JSON.stringify(content);
}

main().catch((err) => {
  console.error('[demo] 出错：', err);
  process.exit(1);
});
