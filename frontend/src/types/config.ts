export interface LLMConfig {
  id: string;
  name: string;
  provider: LLMProvider;
  model: string;
  apiKey?: string;
  baseUrl?: string;
  temperature: number;
  maxTokens: number;
  topP: number;
  enabled: boolean;
}

export type LLMProvider = 
  | 'openai' 
  | 'anthropic' 
  | 'google' 
  | 'qwen' 
  | 'doubao' 
  | 'moonshot' 
  | 'zhipu'
  | 'baidu'
  | 'xfyun'
  | 'test'
  | 'ollama';

export interface ModelInfo {
  id: string;
  name: string;
  provider: LLMProvider;
  maxTokens: number;
  supportsStreaming: boolean;
  supportsVision: boolean;
}

export const PROVIDER_LABELS: Record<LLMProvider, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  google: 'Google',
  qwen: '阿里云通义千问',
  doubao: '字节跳动豆包',
  moonshot: '月之暗面Kimi',
  zhipu: '智谱AI',
  baidu: '百度文心一言',
  xfyun: '讯飞星火',
  test: '测试模型',
  ollama: 'Ollama (本地)',
};

export const PROVIDER_LOGOS: Record<LLMProvider, string> = {
  openai: 'https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg',
  anthropic: 'https://upload.wikimedia.org/wikipedia/commons/4/4a/Claude_icon.svg',
  google: 'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg',
  qwen: 'https://img.alicdn.com/imgextra/i4/OAI-CN20320219_w1200_h1200.png',
  doubao: 'https://www.vipui.cn/uploads/2024/05/31/8f9c5d3e4b1a2.png',
  moonshot: 'https://img.moonshot.cn/default/logo.png',
  ollama: 'https://ollama.com/public/ollama-logo.svg',
};
