/** 统一的接口返回结构 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

/** 支持的模型服务商 */
export type OcrProvider = 'gemini' | 'qwen';

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
}
