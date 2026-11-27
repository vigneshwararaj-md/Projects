import { generateObject } from 'ai';
import { ReviewInsightSchema, type ReviewInsight } from './schemas';
import { resolveModel, type AIConfig } from './provider';

const INSTRUCTIONS = `You review a day using ONLY the provided data.
Rules:
- No cheerleading. No "great job". No generic advice.
- headline: one factual sentence about the day.
- patterns: at most 3. Each MUST cite specific task titles or numbers as evidence. If there is not enough data for a pattern, return fewer patterns (including zero).
- oneChange: one concrete adjustment for tomorrow that could be tested.
- suggestCarryOver: only ids from the "slipped" list, highest priority first.`;

export type ReviewInput = {
  date: string;
  availableMin: number;
  plannedMin: number;
  completed: Array<{ id: string; title: string; priority: string; estimateMin: number; tag: string }>;
  slipped: Array<{ id: string; title: string; priority: string; estimateMin: number; tag: string }>;
  notPlanned: Array<{ id: string; title: string; priority: string; estimateMin: number; tag: string }>;
};

export async function reviewDay(input: ReviewInput, ai: AIConfig): Promise<ReviewInsight> {
  const { object } = await generateObject({
    model: resolveModel(ai),
    schema: ReviewInsightSchema,
    instructions: INSTRUCTIONS,
    prompt: JSON.stringify(input),
    temperature: 0.3,
  });
  return object;
}