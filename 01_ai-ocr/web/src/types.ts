/** 统一的接口返回结构 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

/** 支持的模型服务商 */
export type OcrProvider = 'gemini' | 'qwen';

/** 一条对话消息，格式和 OpenAI 兼容接口的 messages 数组元素一致 */
export interface ChatMessage {
  role: 'user' | 'assistant';
  content:
    | string
    | Array<{ type: 'text'; text: string } | { type: 'image_url'; image_url: { url: string } }>;
}

/** POST /api/ocr/parse 的返回数据 */
export interface OcrData {
  text: string;
  provider: OcrProvider;
  model: string;
  durationMs: number;
  /** 本轮对话历史，追问时原样带上 */
  messages: ChatMessage[];
}

/** POST /api/ocr/chat 的返回数据 */
export interface OcrChatData {
  reply: string;
  messages: ChatMessage[];
}
