import { Module } from '@nestjs/common';
import { OcrModule } from './modules/ocr/ocr.module';

@Module({
  imports: [OcrModule],
})
export class AppModule {}
