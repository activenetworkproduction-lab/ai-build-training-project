import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  // 所有接口统一挂在 /api 下，配合 RouterModule 形成 /api/project1/*、/api/project2/*
  app.setGlobalPrefix('api');
  app.enableCors();
  const port = Number(process.env.PORT) || 3040;
  await app.listen(port);
  console.log(`Server is running on http://localhost:${port}`);
}
bootstrap();
