import {
  BadRequestException,
  Body,
  Controller,
  Post,
  UploadedFile,
  UseInterceptors,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import type { ApiResponse, OcrData, OcrProvider } from '@app/shared';
import { OcrService } from './ocr.service';

/**
 * 【学习要点】图片是怎么从浏览器传到后端的？
 *
 * 前端用 FormData 发起 multipart/form-data 请求（这是文件上传的标准格式），
 * 一个请求里同时携带：文件字段 "image" + 普通文本字段（provider / apiKey / model）。
 *
 * NestJS 的 FileInterceptor('image') 底层是 multer 中间件，它会：
 *   1. 解析 multipart 请求体；
 *   2. 把名为 "image" 的文件放进 @UploadedFile() 参数（file.buffer 就是图片的二进制内容）；
 *   3. 把其余文本字段放进 @Body() 参数。
 */
@Controller()
export class OcrController {
  constructor(private readonly service: OcrService) {}

  // POST /api/ocr/parse
  @Post('parse')
  @UseInterceptors(
    FileInterceptor('image', {
      // 限制上传大小 10MB，超出时 multer 直接报错，不会进入下面的方法
      limits: { fileSize: 10 * 1024 * 1024 },
    }),
  )
  async parse(
    @UploadedFile() file: Express.Multer.File | undefined,
    @Body()
    body: {
      provider?: string;
      apiKey?: string;
      model?: string;
      prompt?: string;
    },
  ): Promise<ApiResponse<OcrData>> {
    // ---- 参数校验：给学习者清晰的错误提示 ----
    if (!file) {
      throw new BadRequestException('缺少文件字段 "image"，请选择一张图片再上传');
    }
    if (!file.mimetype.startsWith('image/')) {
      throw new BadRequestException(`只支持图片文件，收到的类型是 ${file.mimetype}`);
    }
    const provider = (body.provider ?? 'gemini') as OcrProvider;
    if (provider !== 'gemini' && provider !== 'qwen') {
      throw new BadRequestException(`不支持的服务商 "${body.provider}"，可选值：gemini / qwen`);
    }

    const data = await this.service.parseImage(file, {
      provider,
      apiKey: body.apiKey,
      model: body.model,
      prompt: body.prompt,
    });
    return { code: 0, message: 'ok', data };
  }
}
