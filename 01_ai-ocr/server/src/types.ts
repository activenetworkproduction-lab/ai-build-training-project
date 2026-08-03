/** 统一的接口返回结构 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

/** 支持的模型服务商 */
export type OcrProvider = 'gemini' | 'qwen';

/**
 * 一条对话消息，格式和 OpenAI 兼容接口的 messages 数组元素一致。
 * content 可以是纯文本（追问时），也可以是"文字+图片"的数组（只有第一轮携带图片）。
 */
export interface ChatMessage {
  role: 'user' | 'assistant';
  content:
    | string
    | Array<{ type: 'text'; text: string } | { type: 'image_url'; image_url: { url: string } }>;
}

/** POST /api/ocr/parse 的返回数据 */
export interface OcrData {
  /** 模型解析出的图片文字内容 */
  text: string;
  /** 实际使用的服务商 */
  provider: OcrProvider;
  /** 实际使用的模型名 */
  model: string;
  /** 本次解析耗时（毫秒） */
  durationMs: number;
  /**
   * 本轮对话的完整历史（含图片的第一条 user 消息 + 这条 assistant 回复）。
   * 前端原样保存下来，追问时连同新问题一起传回 /api/ocr/chat，
   * 这样模型才能"记得"之前看过的图片和聊过的内容。
   */
  messages: ChatMessage[];
}

/** POST /api/ocr/chat 的返回数据 */
export interface OcrChatData {
  /** 模型对这次追问的回答 */
  reply: string;
  /** 更新后的完整对话历史（追加了这轮的 user 问题 + assistant 回答），前端替换掉本地保存的那份 */
  messages: ChatMessage[];
}
