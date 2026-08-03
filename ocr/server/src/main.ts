import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  // 全局前缀 /api，OcrController 自己挂在 'ocr' 下，最终路由是 /api/ocr/parse
  app.setGlobalPrefix('api');
  app.enableCors();
  const port = Number(process.env.PORT) || 3040;
  await app.listen(port);
  console.log(`Server is running on http://localhost:${port}`);
}
bootstrap();
