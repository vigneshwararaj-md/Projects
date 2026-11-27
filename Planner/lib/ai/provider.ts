import { createGroq } from '@ai-sdk/groq';
import { createOllama } from 'ollama-ai-provider-v2';
import type { LanguageModel } from 'ai';

export type AIConfig = {
  provider: 'groq' | 'ollama';
  model?: string;
  apiKey?: string;
};

export const GROQ_DEFAULT_MODEL = 'openai/gpt-oss-120b';
export const OLLAMA_DEFAULT_MODEL = 'qwen3:8b';

export function resolveModel(ai: AIConfig): LanguageModel {
  if (ai.provider === 'ollama') {
    return createOllama()(ai.model ?? OLLAMA_DEFAULT_MODEL);
  }
  const key = ai.apiKey ?? process.env.GROQ_API_KEY;
  if (!key) throw new Error('No Groq API key. Add one in Settings.');
  return createGroq({ apiKey: key })(ai.model ?? GROQ_DEFAULT_MODEL);
}

export function redact(err: unknown): string {
  const msg = err instanceof Error ? err.message : String(err);
  return msg.replace(/gsk_[A-Za-z0-9]+/g, 'gsk_***');
}