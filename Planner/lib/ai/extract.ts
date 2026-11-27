import { generateObject } from 'ai';
import { ExtractedTasksSchema, type ExtractedTask } from './schemas';
import { resolveModel, type AIConfig } from './provider';

const INSTRUCTIONS = `You convert a brain dump into tasks.
Rules:
- One task = one concrete action. Split compound items ("email Sarah and book flights" -> 2 tasks).
- Title: imperative verb, <= 80 characters. No "I need to".
- P0 only if skipping it today has immediate consequences. P1 = this week. P2 = this month. P3 = someday.
- estimateMin: realistic single-sitting estimate (5-240), not total project time.
- tag = mode of work, used to batch similar tasks. Choose one of the allowed values.
- deadline: YYYY-MM-DD only if stated or clearly implied, otherwise null.
- Never invent tasks. Omit anything that is not actionable.
- Preserve the user's language.`;

export async function extractTasks(text: string, ai: AIConfig): Promise<ExtractedTask[]> {
  const { object } = await generateObject({
    model: resolveModel(ai),
    schema: ExtractedTasksSchema,
    instructions: INSTRUCTIONS,
    prompt: text.slice(0, 8000),
    temperature: 0.2,
  });
  return object.tasks;
}