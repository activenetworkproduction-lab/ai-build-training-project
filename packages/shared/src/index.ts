/** 统一的接口返回结构 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

/** 示例接口 /api/projectN/hello 的返回数据 */
export interface HelloData {
  project: string;
  time: string;
}

/** OCR 项目：支持的模型服务商 */
export type OcrProvider = 'gemini' | 'qwen';

/** OCR 项目：POST /api/ocr/parse 的返回数据 */
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

/** 图片内容识别+分析项目：支持的模型服务商 */
export type VisionProvider = 'gemini' | 'openai';

/** 图片内容识别+分析项目：POST /api/vision-analysis/analyze 的返回数据 */
export interface VisionAnalysisData {
  /** 图片内容的客观描述（画面里有什么） */
  description: string;
  /** 更深一层的分析（场景推断、可能的用途、值得关注的细节等） */
  analysis: string;
  /** 实际使用的服务商 */
  provider: VisionProvider;
  /** 实际使用的模型名 */
  model: string;
  /** 本次调用耗时（毫秒） */
  durationMs: number;
}
