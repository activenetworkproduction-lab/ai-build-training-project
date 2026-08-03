import { Module } from '@nestjs/common';
import { VisionAnalysisController } from './vision-analysis.controller';
import { VisionAnalysisService } from './vision-analysis.service';

@Module({
  controllers: [VisionAnalysisController],
  providers: [VisionAnalysisService],
})
export class VisionAnalysisModule {}
