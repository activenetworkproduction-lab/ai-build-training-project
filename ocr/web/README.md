# OCR 项目：图片上传 → 大模型文字解析（学习指南）

上传一张图片，由视觉大模型（Gemini / Qwen-VL）解析出图片中的文字。
本文档讲清楚两件事：**图片是怎么一步步传给模型的**，以及**怎么配置/更换模型**。

## 一、整体流程

```
浏览器                     OCR 后端 (NestJS)                模型服务商
────────                  ─────────────────               ──────────────
选择图片 (File)
   │
   │ ① FormData + fetch
   │   POST /api/ocr/parse
   │   multipart/form-data
   ▼
FileInterceptor('image')
解析出 file.buffer（二进制）
   │
   │ ② buffer → base64 → data URL
   │   "data:image/png;base64,iVBOR..."
   ▼
组装 OpenAI 兼容请求
   │
   │ ③ POST {baseUrl}/chat/completions
   │   Authorization: Bearer <API Key>
   ▼
                                              模型"看图"识别文字
   ◄──────────────────────────────────────────  ④ choices[0].message.content
展示识别结果
```

对应代码位置：

| 步骤 | 文件 |
|---|---|
| ① 前端上传 | `ocr/web/src/App.tsx` 的 `handleParse()` |
| ① 后端接收 | `ocr/server/src/modules/ocr/ocr.controller.ts` |
| ②③④ 调用模型 | `ocr/server/src/modules/ocr/ocr.service.ts` 的 `parseImage()` |

## 二、三个关键知识点

### 1. 文件上传为什么用 FormData（multipart/form-data）？

JSON 只能装文本，图片是二进制。`FormData` 生成的 `multipart/form-data` 请求
可以在**一个请求里同时装二进制文件和普通文本字段**（本项目里就是图片 + provider/apiKey/model）。

前端注意事项：用 `fetch` 发送 `FormData` 时**不要手动设置 Content-Type**，
浏览器会自动生成带 `boundary`（字段分隔标记）的正确请求头。

### 2. 模型怎么"看到"图片？—— base64 data URL

模型接口收 JSON，JSON 装不下二进制，所以后端把图片编码成 base64 字符串，
拼成 `data:image/png;base64,xxxx` 塞进消息里。多模态消息的 `content` 是一个数组：

```json
{
  "model": "gemini-3.5-flash",
  "messages": [{
    "role": "user",
    "content": [
      { "type": "text", "text": "请提取这张图片中的所有文字…" },
      { "type": "image_url", "image_url": { "url": "data:image/png;base64,iVBOR…" } }
    ]
  }]
}
```

> base64 会让体积膨胀约 1/3，所以后端限制上传 10MB 以内。

### 3. 为什么换服务商不用改代码？—— OpenAI 兼容接口

Gemini 和 Qwen 都提供与 OpenAI `/chat/completions` 完全相同的请求/返回格式，
所以**换服务商只是换三个配置**（见 `ocr.service.ts` 的 `PROVIDER_CONFIG`）：

| 服务商 | baseUrl | 默认模型 | API Key 获取 |
|---|---|---|---|
| Gemini | `https://generativelanguage.googleapis.com/v1beta/openai` | `gemini-3.5-flash` | [Google AI Studio](https://aistudio.google.com/apikey)（免费额度） |
| Qwen | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen3-vl-plus` | [阿里云百炼](https://bailian.console.aliyun.com/) |

## 三、怎么配置 API Key 和更换模型

两种方式，界面填写优先于环境变量：

1. **界面填写（推荐学习时用）**：页面上选服务商、粘贴 API Key、改模型名即可，
   配置保存在浏览器 localStorage，刷新不丢。
2. **服务端环境变量（适合部署）**：启动后端前设置 `GEMINI_API_KEY` 或
   `DASHSCOPE_API_KEY`，前端 Key 留空即可。

   ```powershell
   $env:GEMINI_API_KEY = "你的Key"; pnpm dev:ocr:server
   ```

换模型：直接改页面上的"模型名"输入框（如 `gemini-3.5-flash` 换成其他 Gemini 视觉模型，
或 `qwen3-vl-plus` 换成 `qwen3-vl-max` 等），只要该模型支持图片输入即可。

## 四、常见报错对照

| 报错 | 原因 |
|---|---|
| `缺少 gemini 的 API Key` | 界面没填 Key，服务端也没设环境变量 |
| `HTTP 401` / `API key not valid` | Key 填错或已失效 |
| `HTTP 404` / `model not found` | 模型名写错，或该服务商没有这个模型 |
| `HTTP 429` | 触发限流或额度用完 |
| `无法连接 … 服务` | 网络问题（访问 Gemini 可能需要代理） |
| `只支持图片文件` | 上传了非图片文件 |

## 五、本地运行

```bash
pnpm dev:ocr:server   # 后端 http://localhost:3040
pnpm dev:ocr:web      # 前端 http://localhost:5102
```
