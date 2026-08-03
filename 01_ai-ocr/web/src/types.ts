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
  text: string;
  provider: OcrProvider;
  model: string;
  durationMs: number;
}
