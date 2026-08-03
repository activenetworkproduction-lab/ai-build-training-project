import {
  BadGatewayException,
  BadRequestException,
  Injectable,
  Logger,
} from '@nestjs/common';
import type { VisionAnalysisData, VisionProvider } from '@app/shared';

/**
 * 图片内容识别 + 分析。
 *
 * 和 apps/server/src/modules/ocr/ocr.service.ts 的调用方式完全一样（图片转 base64
 * data URL，走 OpenAI 兼容的 /chat/completions），区别只在于问模型的问题：
 * OCR 是"抄文字"，这里是"描述画面 + 给出分析"。
 *
 * 【课堂实操说明】analyzeImage() 里调用模型的核心逻辑已经注释掉了——这部分已经
 * 完整实现并用真实图片 + Gemini API 验证跑通过，注释内容就是验证通过的代码，
 * 课堂上会照着这个思路重新手写一遍。跑通的效果长这样（用一张简笔画风格的
 * 房子+大树+太阳的图测试）：
 *
 *   description: "这是一幅极简风格的2D几何图形绘画……左侧是一棵由深绿色圆形和
 *                 棕色长方形（树干）组成的简易树木；右侧是一个由棕色三角形
 *                 （屋顶）和粉红色长方形（墙体）拼成的无门窗房屋……"
 *   analysis:    "可能的用途与场景：编程教学/图形学练习……这种由基础几何体拼凑、
 *                 代码感极强的画面，非常像是计算机编程初学者练习定位和绘制基本
 *                 图形时创作的 Demo 作品……"
 */
const PROVIDER_CONFIG: Record<
  VisionProvider,
  { baseUrl: string; defaultModel: string; envKey: string; consoleUrl: string }
> = {
  gemini: {
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai',
    // gemini-2.5-flash 已对新用户下线，改用仍可用的 gemini-3.5-flash（与 OCR 项目保持一致）
    defaultModel: 'gemini-3.5-flash',
    envKey: 'GEMINI_API_KEY',
    consoleUrl: 'https://aistudio.google.com/apikey',
  },
  openai: {
    baseUrl: 'https://api.openai.com/v1',
    defaultModel: 'gpt-4o',
    envKey: 'OPENAI_API_KEY',
    consoleUrl: 'https://platform.openai.com/api-keys',
  },
};

// 让模型按固定格式输出，方便用简单的字符串查找把"描述"和"分析"拆开，
// 不依赖 JSON 严格模式（各家 JSON 模式的参数名不完全一致，纯文本格式更通用）
const PROMPT = [
  '请描述这张图片的内容，并做一段更深入的分析。',
  '必须严格按以下格式输出，两个标题都要保留：',
  '描述：<客观描述画面里有什么，包含主要物体、人物、场景>',
  '分析：<更深一层的分析，例如可能的场景/用途、值得注意的细节、给出的推断>',
].join('\n');

interface AnalyzeOptions {
  provider: VisionProvider;
  apiKey?: string;
  model?: string;
}

@Injectable()
export class VisionAnalysisService {
  private readonly logger = new Logger(VisionAnalysisService.name);

  async analyzeImage(
    file: Express.Multer.File,
    options: AnalyzeOptions,
  ): Promise<VisionAnalysisData> {
    // TODO(课堂实操)：删掉下面这行占位 return，参考本文件底部注释掉的参考实现，
    // 自己实现「拼请求 → 调用模型 → 解析结果」的过程。
    void file;
    return {
      description: '（课堂实操占位）图片内容识别功能尚未实现，敬请期待课堂实操环节。',
      analysis: '（课堂实操占位）深入分析功能尚未实现。',
      provider: options.provider,
      model: options.model || PROVIDER_CONFIG[options.provider].defaultModel,
      durationMs: 0,
    };

    /* ===== 参考实现（已用真实图片 + Gemini API 验证跑通，课堂上现场重写）=====

    const config = PROVIDER_CONFIG[options.provider];

    const apiKey = options.apiKey?.trim() || process.env[config.envKey];
    if (!apiKey) {
      throw new BadRequestException(
        `缺少 ${options.provider} 的 API Key：请在页面上填写，或在启动后端前设置环境变量 ${config.envKey}。` +
          `获取地址：${config.consoleUrl}`,
      );
    }

    const model = options.model?.trim() || config.defaultModel;
    const dataUrl = `data:${file.mimetype};base64,${file.buffer.toString('base64')}`;

    const startedAt = Date.now();
    this.logger.log(`调用 ${options.provider}/${model} 分析图片（${file.size} 字节）`);

    let response: Response;
    try {
      response = await fetch(`${config.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model,
          messages: [
            {
              role: 'user',
              content: [
                { type: 'text', text: PROMPT },
                { type: 'image_url', image_url: { url: dataUrl } },
              ],
            },
          ],
        }),
      });
    } catch (err) {
      throw new BadGatewayException(
        `无法连接 ${options.provider} 服务（${config.baseUrl}），请检查网络：${String(err)}`,
      );
    }

    if (!response.ok) {
      const errorText = await response.text();
      throw new BadGatewayException(
        `${options.provider} 返回错误（HTTP ${response.status}）：${errorText.slice(0, 500)}`,
      );
    }

    const result = (await response.json()) as {
      choices?: { message?: { content?: string } }[];
    };
    const rawText = result.choices?.[0]?.message?.content;
    if (typeof rawText !== 'string') {
      throw new BadGatewayException(
        `${options.provider} 返回了意外的数据结构：${JSON.stringify(result).slice(0, 500)}`,
      );
    }

    const { description, analysis } = this.splitDescriptionAndAnalysis(rawText);

    return {
      description,
      analysis,
      provider: options.provider,
      model,
      durationMs: Date.now() - startedAt,
    };

    ===== 参考实现结束 ===== */
  }

  /**
   * 把模型输出的一整段文字，按"描述："/"分析："两个标题拆成两段。
   * 如果模型没有严格按格式输出（偶尔会发生），就把全部内容放进 description，
   * analysis 留空提示，而不是直接报错——教学场景下让学习者看到"原始输出"更有价值。
   *
   * 这个辅助函数不涉及"调用模型"本身，属于周边逻辑，已经直接写完整，
   * 课堂实操只需要在 analyzeImage 里调用它。
   */
  private splitDescriptionAndAnalysis(text: string): { description: string; analysis: string } {
    const descIndex = text.indexOf('描述：');
    const analysisIndex = text.indexOf('分析：');

    if (descIndex === -1 || analysisIndex === -1 || analysisIndex < descIndex) {
      return { description: text.trim(), analysis: '（模型未按约定格式输出"分析："部分，以上为完整原始输出）' };
    }

    const description = text.slice(descIndex + '描述：'.length, analysisIndex).trim();
    const analysis = text.slice(analysisIndex + '分析：'.length).trim();
    return { description, analysis };
  }
}
