import {
  BadGatewayException,
  BadRequestException,
  Injectable,
  Logger,
} from '@nestjs/common';
import type { ChatMessage, OcrData, OcrProvider } from '../../types';

/**
 * 【学习要点】视觉大模型是怎么"看图"的？
 *
 * 图片本身是二进制数据，没法直接放进 JSON 请求里，所以要先转成 base64 字符串，
 * 拼成 data URL（形如 data:image/png;base64,iVBORw0KG...），再作为消息内容的一部分发给模型。
 *
 * Gemini 和 Qwen（通义千问）都提供 "OpenAI 兼容" 的接口：请求格式和 OpenAI 的
 * /chat/completions 完全一样，只是 baseUrl、模型名、API Key 不同。
 * 所以换服务商 = 换三个配置项，代码逻辑完全不用改 —— 这也是本项目选这种写法的原因。
 *
 * 【学习要点】追问功能是怎么"记住"之前的对话的？
 *
 * 大模型的 API 本身是无状态的——每次调用都是独立的，服务器不会帮你记住上一轮聊了什么。
 * 能"接着聊"全靠客户端每次把完整的历史消息数组（messages）一起发过去，模型看到的是
 * "从头到尾的完整对话"，而不是"新增的这一句"。这也是为什么追问接口 chat() 需要
 * 接收并原样传回 messages：图片只在第一轮出现一次，但只要它还在 messages 数组里，
 * 后面每一轮模型都还能"看见"它。
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

interface ChatOptions {
  provider: OcrProvider;
  apiKey?: string;
  model?: string;
  messages: ChatMessage[];
  question: string;
}

@Injectable()
export class OcrService {
  private readonly logger = new Logger(OcrService.name);

  async parseImage(file: Express.Multer.File, options: ParseOptions): Promise<OcrData> {
    const { apiKey, model, config } = this.resolveCredentials(options);

    // ---- 第 1 步：二进制图片 → base64 data URL ----
    const dataUrl = `data:${file.mimetype};base64,${file.buffer.toString('base64')}`;

    // ---- 第 2 步：组装 OpenAI 兼容的多模态消息（第一轮，图片只在这里出现一次）----
    // content 是一个数组：一段文字指令 + 一张图片，模型会把两者放在一起理解
    const firstMessage: ChatMessage = {
      role: 'user',
      content: [
        { type: 'text', text: options.prompt?.trim() || DEFAULT_PROMPT },
        { type: 'image_url', image_url: { url: dataUrl } },
      ],
    };

    // ---- 第 3 步：调用模型接口 ----
    const startedAt = Date.now();
    this.logger.log(`调用 ${options.provider}/${model} 解析图片（${file.size} 字节）`);
    const text = await this.callModel(config, apiKey, model, [firstMessage]);

    return {
      text,
      provider: options.provider,
      model,
      durationMs: Date.now() - startedAt,
      // 保存下这轮对话，前端追问时会把它原样传回来，再往后追加新的问答
      messages: [firstMessage, { role: 'assistant', content: text }],
    };
  }

  /**
   * 追问：把"到目前为止的完整对话历史 + 新问题"一起发给模型。
   * 历史里的第一条消息带着图片，所以模型依然能回答"图片里那个电话号码是多少"这类问题。
   */
  async chat(options: ChatOptions): Promise<{ reply: string; messages: ChatMessage[] }> {
    const { apiKey, model, config } = this.resolveCredentials(options);

    const messages: ChatMessage[] = [
      ...options.messages,
      { role: 'user', content: options.question },
    ];

    this.logger.log(`调用 ${options.provider}/${model} 追问（第 ${messages.length} 条消息）`);
    const reply = await this.callModel(config, apiKey, model, messages);

    return { reply, messages: [...messages, { role: 'assistant', content: reply }] };
  }

  private resolveCredentials(options: { provider: OcrProvider; apiKey?: string; model?: string }) {
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
    return { apiKey, model, config };
  }

  /** 真正发请求给模型、取出文字回复——parseImage 和 chat 共用这一段逻辑。 */
  private async callModel(
    config: { baseUrl: string },
    apiKey: string,
    model: string,
    messages: ChatMessage[],
  ): Promise<string> {
    let response: Response;
    try {
      response = await fetch(`${config.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({ model, messages }),
      });
    } catch (err) {
      throw new BadGatewayException(`无法连接模型服务（${config.baseUrl}），请检查网络：${String(err)}`);
    }

    if (!response.ok) {
      // 把服务商返回的原始错误透传给前端，方便学习者排查（Key 错误 / 模型名不存在 / 欠费等）
      const errorText = await response.text();
      throw new BadGatewayException(`模型返回错误（HTTP ${response.status}）：${errorText.slice(0, 500)}`);
    }

    // OpenAI 兼容接口的返回结构：{ choices: [ { message: { content: "回复内容" } } ] }
    const result = (await response.json()) as {
      choices?: { message?: { content?: string } }[];
    };
    const text = result.choices?.[0]?.message?.content;
    if (typeof text !== 'string') {
      throw new BadGatewayException(`模型返回了意外的数据结构：${JSON.stringify(result).slice(0, 500)}`);
    }
    return text;
  }
}
