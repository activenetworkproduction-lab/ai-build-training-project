import { NestFactory } from '@nestjs/core';
import { json } from 'express';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  // 全局前缀 /api，OcrController 自己挂在 'ocr' 下，最终路由是 /api/ocr/parse
  app.setGlobalPrefix('api');
  app.enableCors();

  // /api/ocr/chat 的请求体里带着完整对话历史（含第一轮的 base64 图片，最大能有
  // 10MB 图片对应约 13-14MB 的 base64 文本），Express 默认的 JSON body 限制是 100kb，
  // 不调大这里的话追问接口会直接报 413 Payload Too Large。
  app.use(json({ limit: '15mb' }));

  const port = Number(process.env.PORT) || 3040;
  await app.listen(port);
  console.log(`Server is running on http://localhost:${port}`);
}
bootstrap();
