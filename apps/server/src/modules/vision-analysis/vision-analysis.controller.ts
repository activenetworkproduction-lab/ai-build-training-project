import {
  BadRequestException,
  Body,
  Controller,
  Post,
  UploadedFile,
  UseInterceptors,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import type { ApiResponse, VisionAnalysisData, VisionProvider } from '@app/shared';
import { VisionAnalysisService } from './vision-analysis.service';

/**
 * 【骨架阶段说明】
 * 上传/请求参数的结构与 ocr 项目（apps/server/src/modules/ocr）完全一致，
 * 区别只在于 service 里让模型做什么：OCR 是"抄下图里的文字"，
 * 这个项目是"描述图里有什么 + 给出进一步分析"。
 * 具体的模型调用会在细化阶段实现，详见 vision-analysis.service.ts。
 */
@Controller()
export class VisionAnalysisController {
  constructor(private readonly service: VisionAnalysisService) {}

  // POST /api/vision-analysis/analyze
  @Post('analyze')
  @UseInterceptors(FileInterceptor('image', { limits: { fileSize: 10 * 1024 * 1024 } }))
  async analyze(
    @UploadedFile() file: Express.Multer.File | undefined,
    @Body()
    body: { provider?: string; apiKey?: string; model?: string },
  ): Promise<ApiResponse<VisionAnalysisData>> {
    if (!file) {
      throw new BadRequestException('缺少文件字段 "image"，请选择一张图片再上传');
    }
    if (!file.mimetype.startsWith('image/')) {
      throw new BadRequestException(`只支持图片文件，收到的类型是 ${file.mimetype}`);
    }
    const provider = (body.provider ?? 'gemini') as VisionProvider;
    if (provider !== 'gemini' && provider !== 'openai') {
      throw new BadRequestException(`不支持的服务商 "${body.provider}"，可选值：gemini / openai`);
    }

    const data = await this.service.analyzeImage(file, {
      provider,
      apiKey: body.apiKey,
      model: body.model,
    });
    return { code: 0, message: 'ok', data };
  }
}
