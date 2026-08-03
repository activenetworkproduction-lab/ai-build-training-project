import {
  BadGatewayException,
  BadRequestException,
  Injectable,
  Logger,
} from '@nestjs/common';
import type { OcrData, OcrProvider } from '@app/shared';

/**
 * 【学习要点】视觉大模型是怎么"看图"的？
 *
 * 图片本身是二进制数据，没法直接放进 JSON 请求里，所以要先转成 base64 字符串，
 * 拼成 data URL（形如 data:image/png;base64,iVBORw0KG...），再作为消息内容的一部分发给模型。
 *
 * Gemini 和 Qwen（通义千问）都提供 "OpenAI 兼容" 的接口：请求格式和 OpenAI 的
 * /chat/completions 完全一样，只是 baseUrl、模型名、API Key 不同。
 * 所以换服务商 = 换三个配置项，代码逻辑完全不用改 —— 这也是本项目选这种写法的原因。
 */

/** 各服务商的接入配置：换模型/换服务商时改这里（或直接在前端界面填写） */
const PROVIDER_CONFIG: Record<
  OcrProvider,
  { baseUrl: string; defaultModel: string; envKey: string; consoleUrl: string }
> = {
  gemini: {
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai',
    defaultModel: 'gemini-3.5-flash',
    envKey: 'GEMINI_API_KEY',
    consoleUrl: 'https://aistudio.google.com/apikey',
  },
  qwen: {
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    defaultModel: 'qwen3-vl-plus',
    envKey: 'DASHSCOPE_API_KEY',
    consoleUrl: 'https://bailian.console.aliyun.com/',
  },
};

/** 默认提示词：告诉模型"只做 OCR，不要发挥" */
const DEFAULT_PROMPT =
  '请提取这张图片中的所有文字内容，按原有排版尽量保留换行，直接输出文字，不要添加任何解释或说明。';

interface ParseOptions {
  provider: OcrProvider;
  apiKey?: string;
  model?: string;
  prompt?: string;
}

@Injectable()
export class OcrService {
  private readonly logger = new Logger(OcrService.name);

  async parseImage(file: Express.Multer.File, options: ParseOptions): Promise<OcrData> {
    const config = PROVIDER_CONFIG[options.provider];

    // API Key 优先级：前端界面填写的 > 服务端环境变量（GEMINI_API_KEY / DASHSCOPE_API_KEY）
    const apiKey = options.apiKey?.trim() || process.env[config.envKey];
    if (!apiKey) {
      throw new BadRequestException(
        `缺少 ${options.provider} 的 API Key：请在页面上填写，或在启动后端前设置环境变量 ${config.envKey}。` +
          `获取地址：${config.consoleUrl}`,
      );
    }

    const model = options.model?.trim() || config.defaultModel;

    // ---- 第 1 步：二进制图片 → base64 data URL ----
    const dataUrl = `data:${file.mimetype};base64,${file.buffer.toString('base64')}`;

    // ---- 第 2 步：组装 OpenAI 兼容的多模态消息 ----
    // content 是一个数组：一段文字指令 + 一张图片，模型会把两者放在一起理解
    const requestBody = {
      model,
      messages: [
        {
          role: 'user',
          content: [
            { type: 'text', text: options.prompt?.trim() || DEFAULT_PROMPT },
            { type: 'image_url', image_url: { url: dataUrl } },
          ],
        },
      ],
    };

    // ---- 第 3 步：调用模型接口 ----
    const startedAt = Date.now();
    this.logger.log(`调用 ${options.provider}/${model} 解析图片（${file.size} 字节）`);

    let response: Response;
    try {
      response = await fetch(`${config.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify(requestBody),
      });
    } catch (err) {
      throw new BadGatewayException(
        `无法连接 ${options.provider} 服务（${config.baseUrl}），请检查网络：${String(err)}`,
      );
    }

    if (!response.ok) {
      // 把服务商返回的原始错误透传给前端，方便学习者排查（Key 错误 / 模型名不存在 / 欠费等）
      const errorText = await response.text();
      throw new BadGatewayException(
        `${options.provider} 返回错误（HTTP ${response.status}）：${errorText.slice(0, 500)}`,
      );
    }

    // ---- 第 4 步：从返回结果中取出文字 ----
    // OpenAI 兼容接口的返回结构：{ choices: [ { message: { content: "识别出的文字" } } ] }
    const result = (await response.json()) as {
      choices?: { message?: { content?: string } }[];
    };
    const text = result.choices?.[0]?.message?.content;
    if (typeof text !== 'string') {
      throw new BadGatewayException(
        `${options.provider} 返回了意外的数据结构：${JSON.stringify(result).slice(0, 500)}`,
      );
    }

    return {
      text,
      provider: options.provider,
      model,
      durationMs: Date.now() - startedAt,
    };
  }
}
