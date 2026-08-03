import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import ExcelJS from 'exceljs';
import { z } from 'zod';

/**
 * 【学习要点】这是一个最小可运行的 MCP Server。
 *
 * MCP（Model Context Protocol）本质上是一套 JSON-RPC 协议：AI 客户端（比如 Claude Desktop、
 * 或我们下面自己写的 client-demo.ts）通过 stdin/stdout 跟这个进程"对话"：
 *   1. 客户端发 initialize 请求，服务端回自己的名字/版本/能力
 *   2. 客户端发 tools/list 请求，服务端把自己注册的工具列表（名字+参数schema+说明）发回去
 *   3. 客户端发 tools/call 请求（带上工具名+参数），服务端执行对应函数，把结果发回去
 *
 * McpServer 是 SDK 提供的高层封装，帮我们处理了上面这套协议细节，
 * 我们只需要用 registerTool() 声明"有哪些工具、参数长什么样、怎么执行"。
 */
const server = new McpServer({
  name: 'excel-mcp-server',
  version: '0.0.1',
});

// 出于安全考虑，只允许访问这个目录下的 Excel 文件，不能用 filePath 参数逃逸到任意路径
const SAMPLE_DATA_DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'sample-data');

function resolveSafePath(fileName: string): string {
  const resolved = path.resolve(SAMPLE_DATA_DIR, fileName);
  if (!resolved.startsWith(SAMPLE_DATA_DIR)) {
    throw new Error(`不允许访问 sample-data 目录之外的文件：${fileName}`);
  }
  return resolved;
}

server.registerTool(
  'ping',
  {
    title: 'Ping',
    description: '最小示例工具：用来验证 MCP 握手是否成功，原样返回你传入的消息',
    inputSchema: { message: z.string().describe('任意文本，会被原样返回') },
  },
  async ({ message }) => {
    return {
      content: [{ type: 'text', text: `pong: ${message}` }],
    };
  },
);

server.registerTool(
  'list_sheets',
  {
    title: '列出工作表',
    description: '列出某个 Excel 文件里有哪些工作表（sheet），以及每个工作表的行数/列数',
    inputSchema: {
      fileName: z.string().describe('sample-data 目录下的文件名，例如 company.xlsx'),
    },
  },
  async ({ fileName }) => {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(resolveSafePath(fileName));

    const sheets = workbook.worksheets.map((sheet) => ({
      name: sheet.name,
      rowCount: sheet.rowCount,
      columnCount: sheet.columnCount,
    }));

    return {
      content: [{ type: 'text', text: JSON.stringify(sheets, null, 2) }],
    };
  },
);

server.registerTool(
  'query_sheet',
  {
    title: '查询工作表内容',
    description:
      '读取某个工作表的数据，第一行当作表头，返回一个对象数组（每行一个对象，key 是表头，value 是单元格内容）',
    inputSchema: {
      fileName: z.string().describe('sample-data 目录下的文件名，例如 company.xlsx'),
      sheetName: z.string().describe('工作表名称，用 list_sheets 工具先查出来'),
      maxRows: z.number().int().positive().optional().describe('最多返回多少行数据，默认 50'),
    },
  },
  async ({ fileName, sheetName, maxRows }) => {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(resolveSafePath(fileName));

    const sheet = workbook.getWorksheet(sheetName);
    if (!sheet) {
      throw new Error(`工作表 "${sheetName}" 不存在，可用工作表：${workbook.worksheets.map((s) => s.name).join(', ')}`);
    }

    // 第一行是表头
    const headerRow = sheet.getRow(1);
    const headers: string[] = [];
    headerRow.eachCell({ includeEmpty: false }, (cell, colNumber) => {
      headers[colNumber] = String(cell.value ?? '');
    });

    const rows: Record<string, unknown>[] = [];
    const limit = maxRows ?? 50;
    for (let rowNumber = 2; rowNumber <= sheet.rowCount && rows.length < limit; rowNumber++) {
      const row = sheet.getRow(rowNumber);
      const record: Record<string, unknown> = {};
      row.eachCell({ includeEmpty: false }, (cell, colNumber) => {
        const header = headers[colNumber];
        if (header) record[header] = cell.value;
      });
      if (Object.keys(record).length > 0) rows.push(record);
    }

    return {
      content: [{ type: 'text', text: JSON.stringify(rows, null, 2) }],
    };
  },
);

server.registerTool(
  'search_excel',
  {
    title: '搜索关键字',
    description: '在 Excel 文件的所有工作表里搜索包含指定关键字的单元格，返回命中的位置和整行内容',
    inputSchema: {
      fileName: z.string().describe('sample-data 目录下的文件名，例如 company.xlsx'),
      keyword: z.string().describe('要搜索的关键字，大小写不敏感，支持中英文子串匹配'),
    },
  },
  async ({ fileName, keyword }) => {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(resolveSafePath(fileName));

    const lowerKeyword = keyword.toLowerCase();
    const matches: { sheet: string; row: number; matchedCell: string; rowValues: unknown[] }[] = [];

    for (const sheet of workbook.worksheets) {
      sheet.eachRow((row, rowNumber) => {
        let matchedCell: string | undefined;
        row.eachCell({ includeEmpty: false }, (cell, colNumber) => {
          if (matchedCell) return;
          const text = String(cell.value ?? '').toLowerCase();
          if (text.includes(lowerKeyword)) {
            matchedCell = `列${colNumber}`;
          }
        });
        if (matchedCell) {
          matches.push({
            sheet: sheet.name,
            row: rowNumber,
            matchedCell,
            rowValues: Array.isArray(row.values) ? row.values.slice(1) : [],
          });
        }
      });
    }

    return {
      content: [{ type: 'text', text: JSON.stringify(matches, null, 2) }],
    };
  },
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // 注意：MCP 用 stdout 传输协议消息，所以日志只能打到 stderr，不能用 console.log
  console.error('[excel-mcp-server] 已启动，通过 stdio 等待客户端连接…');
}

main().catch((err) => {
  console.error('[excel-mcp-server] 启动失败：', err);
  process.exit(1);
});
