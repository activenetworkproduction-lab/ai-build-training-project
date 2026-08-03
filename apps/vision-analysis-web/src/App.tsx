import { useEffect, useMemo, useState } from 'react';
import type { ApiResponse, VisionAnalysisData, VisionProvider } from '@app/shared';

/**
 * 图片内容识别 + 分析。
 *
 * 前端结构和 apps/ocr-web 几乎一样（上传/预览/服务商配置/结果展示），
 * 因为"把图片传给视觉大模型"这套 UI 交互本来就是通用的。
 * 唯一的区别是这里问模型的问题不是"抄文字"，而是"这张图里有什么、说明了什么"。
 *
 * 后端 /api/vision-analysis/analyze 目前是骨架阶段的占位实现（固定返回一段提示文字），
 * 真正调用 Gemini 2.5 Flash / OpenAI 视觉模型的部分会在课堂上现场实现。
 */

const PROVIDER_PRESETS: Record<
  VisionProvider,
  { label: string; defaultModel: string; keyHint: string }
> = {
  gemini: {
    label: 'Google Gemini',
    // gemini-2.5-flash 已对新用户下线，改用仍可用的 gemini-3.5-flash
    defaultModel: 'gemini-3.5-flash',
    keyHint: '在 https://aistudio.google.com/apikey 免费申请',
  },
  openai: {
    label: 'OpenAI',
    defaultModel: 'gpt-4o',
    keyHint: '在 https://platform.openai.com/api-keys 申请',
  },
};

const STORAGE_KEY = 'vision-analysis-web-settings';

interface Settings {
  provider: VisionProvider;
  apiKeys: Record<VisionProvider, string>;
  models: Record<VisionProvider, string>;
}

function loadSettings(): Settings {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return JSON.parse(saved) as Settings;
  } catch {
    /* 存储内容损坏时忽略，用默认值 */
  }
  return {
    provider: 'gemini',
    apiKeys: { gemini: '', openai: '' },
    models: {
      gemini: PROVIDER_PRESETS.gemini.defaultModel,
      openai: PROVIDER_PRESETS.openai.defaultModel,
    },
  };
}

export default function App() {
  const [settings, setSettings] = useState<Settings>(loadSettings);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VisionAnalysisData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }, [settings]);

  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const preset = PROVIDER_PRESETS[settings.provider];
  const apiKey = settings.apiKeys[settings.provider];
  const model = settings.models[settings.provider];

  async function handleAnalyze() {
    if (!file) {
      setError('请先选择一张图片');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('provider', settings.provider);
      formData.append('apiKey', apiKey);
      formData.append('model', model);

      const response = await fetch('/api/vision-analysis/analyze', {
        method: 'POST',
        body: formData,
      });

      const json = (await response.json()) as ApiResponse<VisionAnalysisData> & {
        message?: string;
      };
      if (!response.ok || json.code !== 0) {
        throw new Error(json.message ?? `请求失败（HTTP ${response.status}）`);
      }
      setResult(json.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ fontFamily: 'sans-serif', maxWidth: 720, margin: '0 auto', padding: 24 }}>
      <h1>图片内容识别与分析</h1>
      <p style={{ color: '#666' }}>
        上传一张图片，由视觉大模型（Gemini 3.5 Flash / OpenAI 视觉模型）描述画面内容并给出进一步分析。
      </p>
      <p style={{ padding: 8, background: '#fff8e1', borderRadius: 6, fontSize: 13, color: '#7a5c00' }}>
        当前为课堂实操留白：后端的模型调用已经实现并验证跑通，核心代码注释掉了，会在课堂上现场重写。
      </p>

      <fieldset style={{ marginBottom: 16, padding: 16, border: '1px solid #ddd', borderRadius: 8 }}>
        <legend>模型配置（保存在本浏览器，不会上传到别处）</legend>

        <label style={{ display: 'block', marginBottom: 8 }}>
          服务商：
          <select
            value={settings.provider}
            onChange={(e) =>
              setSettings({ ...settings, provider: e.target.value as VisionProvider })
            }
            style={{ marginLeft: 8 }}
          >
            {(Object.keys(PROVIDER_PRESETS) as VisionProvider[]).map((p) => (
              <option key={p} value={p}>
                {PROVIDER_PRESETS[p].label}
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: 'block', marginBottom: 4 }}>
          API Key：
          <input
            type="password"
            value={apiKey}
            placeholder={preset.keyHint}
            onChange={(e) =>
              setSettings({
                ...settings,
                apiKeys: { ...settings.apiKeys, [settings.provider]: e.target.value },
              })
            }
            style={{ marginLeft: 8, width: 360 }}
          />
        </label>
        <p style={{ margin: '0 0 12px', fontSize: 12, color: '#999' }}>{preset.keyHint}</p>

        <label style={{ display: 'block' }}>
          模型名：
          <input
            type="text"
            value={model}
            onChange={(e) =>
              setSettings({
                ...settings,
                models: { ...settings.models, [settings.provider]: e.target.value },
              })
            }
            style={{ marginLeft: 8, width: 240 }}
          />
          <span style={{ marginLeft: 8, fontSize: 12, color: '#999' }}>
            例如 {preset.defaultModel}
          </span>
        </label>
      </fieldset>

      <fieldset style={{ marginBottom: 16, padding: 16, border: '1px solid #ddd', borderRadius: 8 }}>
        <legend>选择图片</legend>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => {
            setFile(e.target.files?.[0] ?? null);
            setResult(null);
            setError(null);
          }}
        />
        {previewUrl && (
          <div style={{ marginTop: 12 }}>
            <img
              src={previewUrl}
              alt="待分析的图片预览"
              style={{ maxWidth: '100%', maxHeight: 300, border: '1px solid #eee' }}
            />
          </div>
        )}
      </fieldset>

      <button
        onClick={handleAnalyze}
        disabled={loading || !file}
        style={{ padding: '8px 24px', fontSize: 16, cursor: loading ? 'wait' : 'pointer' }}
      >
        {loading ? '分析中…' : '开始分析'}
      </button>

      {error && (
        <pre
          style={{
            marginTop: 16,
            padding: 12,
            background: '#fff0f0',
            color: '#c00',
            whiteSpace: 'pre-wrap',
            borderRadius: 8,
          }}
        >
          {error}
        </pre>
      )}
      {result && (
        <section style={{ marginTop: 16 }}>
          <p style={{ fontSize: 12, color: '#999' }}>
            模型：{result.provider}/{result.model}　耗时：{(result.durationMs / 1000).toFixed(1)} 秒
          </p>
          <h2>内容描述</h2>
          <pre style={{ padding: 12, background: '#f6f8fa', whiteSpace: 'pre-wrap', borderRadius: 8 }}>
            {result.description}
          </pre>
          <h2>深入分析</h2>
          <pre style={{ padding: 12, background: '#f6f8fa', whiteSpace: 'pre-wrap', borderRadius: 8 }}>
            {result.analysis}
          </pre>
        </section>
      )}
    </main>
  );
}
