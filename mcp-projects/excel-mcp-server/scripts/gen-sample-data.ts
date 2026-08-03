/**
 * 生成 sample-data/company.xlsx，供 MCP 工具演示查询用。
 * 用法：pnpm --filter excel-mcp-server gen-sample
 */
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ExcelJS from 'exceljs';

const outputPath = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  '..',
  'sample-data',
  'company.xlsx',
);

async function main() {
  const workbook = new ExcelJS.Workbook();

  const employees = workbook.addWorksheet('员工');
  employees.addRow(['姓名', '部门', '职位', '月薪']);
  employees.addRow(['张伟', '技术部', 'CEO', 50000]);
  employees.addRow(['李娜', '技术部', '技术总监', 35000]);
  employees.addRow(['王芳', '产品部', '产品经理', 28000]);
  employees.addRow(['赵磊', '技术部', '后端工程师', 22000]);
  employees.addRow(['陈静', '市场部', '市场专员', 15000]);

  const products = workbook.addWorksheet('产品');
  products.addRow(['产品名称', '分类', '单价', '库存']);
  products.addRow(['云记 - 个人版', '软件订阅', 29, 999999]);
  products.addRow(['云记 - 团队版', '软件订阅', 199, 999999]);
  products.addRow(['云记 - 企业版', '软件订阅', 999, 999999]);

  await workbook.xlsx.writeFile(outputPath);
  console.log(`已生成样例文件：${outputPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
