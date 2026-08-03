import { useEffect, useMemo, useState } from 'react';
import type { ApiResponse, ChatMessage, OcrChatData, OcrData, OcrProvider } from './types';

/**
 * 【学习要点】整个 OCR 流程一共 4 步：
 *
 *   1. 用户在浏览器选择图片（<input type="file">，拿到一个 File 对象）
 *   2. 前端把 File + 配置项装进 FormData，POST 到后端 /api/ocr/parse
 *      —— FormData 会自动生成 multipart/form-data 请求，这是文件上传的标准做法
 *   3. 后端把图片转成 base64，发给视觉大模型（Gemini / Qwen）
 *   4. 模型返回识别出的文字，后端原样传回前端展示，同时带回这一轮的完整对话历史
 *
 * 【学习要点】"继续追问"是怎么做到的？
 *
 * 模型的对话接口本身是无状态的：每次调用都要把"到目前为止聊了什么"完整发一遍，
 * 模型才知道上下文。/parse 的返回结果里有一个 messages 数组（第一条带着图片，
 * 第二条是模型的识别结果），前端原样存在 state 里；每次追问时，把这个数组
 * 连同新问题一起 POST 给 /api/ocr/chat，后端把它们拼起来再发给模型——
 * 这样模型才能"记得"图片长什么样、之前问过什么。
 *
 * API Key 和模型名都在页面上配置，保存在浏览器 localStorage 里，
 * 换模型 = 改一下输入框，不用改任何代码。
 */

/** 每个服务商的默认模型和说明（只影响输入框的默认值，随时可以在界面上改） */
const PROVIDER_PRESETS: Record<
  OcrProvider,
  { label: string; defaultModel: string; keyHint: string }
> = {
  gemini: {
    label: 'Google Gemini',
    defaultModel: 'gemini-3.5-flash',
    keyHint: '在 https://aistudio.google.com/apikey 免费申请',
  },
  qwen: {
    label: '阿里云 通义千问 Qwen-VL',
    defaultModel: 'qwen3-vl-plus',
    keyHint: '在阿里云百炼控制台 https://bailian.console.aliyun.com/ 申请',
  },
};

/** localStorage 的 key：刷新页面后配置不丢失 */
const STORAGE_KEY = 'ocr-web-settings';

interface Settings {
  provider: OcrProvider;
  /** 每个服务商各存一份 key 和模型名，切换服务商时互不覆盖 */
  apiKeys: Record<OcrProvider, string>;
  models: Record<OcrProvider, string>;
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
    apiKeys: { gemini: '', qwen: '' },
    models: {
      gemini: PROVIDER_PRESETS.gemini.defaultModel,
      qwen: PROVIDER_PRESETS.qwen.defaultModel,
    },
  };
}

/** 把 content（可能是纯文本，也可能是"文字+图片"数组）转成一段能展示的文字 */
function messageText(content: ChatMessage['content']): string {
  if (typeof content === 'string') return content;
  return content.find((part) => part.type === 'text')?.text ?? '';
}

export default function App() {
  const [settings, setSettings] = useState<Settings>(loadSettings);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OcrData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 追问相关的状态：完整对话历史（含图片那一条）+ 输入框内容 + 是否正在等回复
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);

  // 配置一变化就写回 localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }, [settings]);

  // 【学习要点】图片预览：URL.createObjectURL 为本地文件生成一个临时地址，
  // 不需要上传就能在 <img> 里显示。组件卸载或换图时要 revoke 释放内存。
  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const preset = PROVIDER_PRESETS[settings.provider];
  const apiKey = settings.apiKeys[settings.provider];
  const model = settings.models[settings.provider];

  async function handleParse() {
    if (!file) {
      setError('请先选择一张图片');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    setMessages([]);
    setChatError(null);

    try {
      // 【学习要点】FormData：一个请求同时携带文件和文本字段。
      // 注意不要手动设置 Content-Type，浏览器会自动加上
      // "multipart/form-data; boundary=..."，boundary 是分隔各字段的标记。
      const formData = new FormData();
      formData.append('image', file); // 文件字段，后端用 FileInterceptor('image') 接收
      formData.append('provider', settings.provider);
      formData.append('apiKey', apiKey);
      formData.append('model', model);

      const response = await fetch('/api/ocr/parse', {
        method: 'POST',
        body: formData,
      });

      const json = (await response.json()) as ApiResponse<OcrData> & { message?: string };
      if (!response.ok || json.code !== 0) {
        // 后端会把参数错误 / 模型服务商的报错信息放在 message 里
        throw new Error(json.message ?? `请求失败（HTTP ${response.status}）`);
      }
      setResult(json.data);
      setMessages(json.data.messages);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleAsk() {
    const q = question.trim();
    if (!q) return;

    setAsking(true);
    setChatError(null);
    // 先把用户的问题加到界面上（乐观更新），回复回来之后再整体替换成后端返回的最新历史
    setMessages((prev) => [...prev, { role: 'user', content: q }]);
    setQuestion('');

    try {
      const response = await fetch('/api/ocr/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: settings.provider,
          apiKey,
          model,
          messages, // 追问之前的历史（不含刚输入的这一句，后端会拼上）
          question: q,
        }),
      });

      const json = (await response.json()) as ApiResponse<OcrChatData> & { message?: string };
      if (!response.ok || json.code !== 0) {
        throw new Error(json.message ?? `请求失败（HTTP ${response.status}）`);
      }
      setMessages(json.data.messages);
    } catch (err) {
      setChatError(err instanceof Error ? err.message : String(err));
      // 请求失败时把刚才乐观加上的那句用户提问撤回，避免界面显示"提问了但没有回答"
      setMessages((prev) => prev.slice(0, -1));
      setQuestion(q);
    } finally {
      setAsking(false);
    }
  }

  // 第 0、1 条消息分别是"图片+初始指令"和"OCR 结果"，已经在"解析结果"区域展示过了，
  // 追问区域只展示第 2 条开始的内容（真正的多轮问答）
  const followUpMessages = messages.slice(2);

  return (
    <main style={{ fontFamily: 'sans-serif', maxWidth: 720, margin: '0 auto', padding: 24 }}>
      <h1>图片文字解析（OCR）</h1>
      <p style={{ color: '#666' }}>
        上传一张图片，由视觉大模型（Gemini / Qwen-VL）解析出其中的文字内容，之后还能继续追问。
      </p>

      {/* ---------- 模型配置区 ---------- */}
      <fieldset style={{ marginBottom: 16, padding: 16, border: '1px solid #ddd', borderRadius: 8 }}>
        <legend>模型配置（保存在本浏览器，不会上传到别处）</legend>

        <label style={{ display: 'block', marginBottom: 8 }}>
          服务商：
          <select
            value={settings.provider}
            onChange={(e) =>
              setSettings({ ...settings, provider: e.target.value as OcrProvider })
            }
            style={{ marginLeft: 8 }}
          >
            {(Object.keys(PROVIDER_PRESETS) as OcrProvider[]).map((p) => (
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
            想换模型直接改这里，例如 {preset.defaultModel}
          </span>
        </label>
      </fieldset>

      {/* ---------- 图片上传区 ---------- */}
      <fieldset style={{ marginBottom: 16, padding: 16, border: '1px solid #ddd', borderRadius: 8 }}>
        <legend>选择图片</legend>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => {
            setFile(e.target.files?.[0] ?? null);
            setResult(null);
            setError(null);
            setMessages([]);
            setChatError(null);
          }}
        />
        {previewUrl && (
          <div style={{ marginTop: 12 }}>
            <img
              src={previewUrl}
              alt="待解析的图片预览"
              style={{ maxWidth: '100%', maxHeight: 300, border: '1px solid #eee' }}
            />
          </div>
        )}
      </fieldset>

      <button
        onClick={handleParse}
        disabled={loading || !file}
        style={{ padding: '8px 24px', fontSize: 16, cursor: loading ? 'wait' : 'pointer' }}
      >
        {loading ? '解析中…（大图可能需要十几秒）' : '开始解析'}
      </button>

      {/* ---------- 结果展示区 ---------- */}
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
          <h2>解析结果</h2>
          <p style={{ fontSize: 12, color: '#999' }}>
            模型：{result.provider}/{result.model}　耗时：{(result.durationMs / 1000).toFixed(1)} 秒
          </p>
          <pre
            style={{
              padding: 12,
              background: '#f6f8fa',
              whiteSpace: 'pre-wrap',
              borderRadius: 8,
            }}
          >
            {result.text}
          </pre>

          {/* ---------- 继续追问区 ---------- */}
          <h2 style={{ marginTop: 24 }}>继续追问</h2>
          <p style={{ fontSize: 12, color: '#999', marginTop: -8 }}>
            针对刚才这张图片接着问，比如"这张表格里的电话号码是多少" "帮我把这段翻译成英文"。
          </p>

          {followUpMessages.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              {followUpMessages.map((m, i) => (
                <div
                  key={i}
                  style={{
                    margin: '8px 0',
                    padding: 10,
                    borderRadius: 8,
                    whiteSpace: 'pre-wrap',
                    background: m.role === 'user' ? '#e8f0fe' : '#f6f8fa',
                    marginLeft: m.role === 'user' ? 40 : 0,
                    marginRight: m.role === 'user' ? 0 : 40,
                  }}
                >
                  <strong>{m.role === 'user' ? '我' : '模型'}：</strong>
                  {messageText(m.content)}
                </div>
              ))}
            </div>
          )}

          {chatError && (
            <pre
              style={{
                padding: 12,
                background: '#fff0f0',
                color: '#c00',
                whiteSpace: 'pre-wrap',
                borderRadius: 8,
              }}
            >
              {chatError}
            </pre>
          )}

          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !asking) handleAsk();
              }}
              placeholder="输入你的问题，回车发送"
              style={{ flex: 1, padding: 8 }}
              disabled={asking}
            />
            <button onClick={handleAsk} disabled={asking || !question.trim()} style={{ padding: '8px 16px' }}>
              {asking ? '提问中…' : '发送'}
            </button>
          </div>
        </section>
      )}
    </main>
  );
}
