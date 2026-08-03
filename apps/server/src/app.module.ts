import { Module } from '@nestjs/common';
import { RouterModule } from '@nestjs/core';
import { Project1Module } from './modules/project1/project1.module';
import { Project2Module } from './modules/project2/project2.module';
import { OcrModule } from './modules/ocr/ocr.module';
import { VisionAnalysisModule } from './modules/vision-analysis/vision-analysis.module';

@Module({
  imports: [
    Project1Module,
    Project2Module,
    OcrModule,
    VisionAnalysisModule,
    // 每个项目的模块挂到各自的路由前缀下，新项目在这里追加一条即可
    RouterModule.register([
      { path: 'project1', module: Project1Module },
      { path: 'project2', module: Project2Module },
      { path: 'ocr', module: OcrModule },
      { path: 'vision-analysis', module: VisionAnalysisModule },
    ]),
  ],
})
export class AppModule {}
