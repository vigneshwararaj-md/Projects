import { generateObject } from 'ai';
import { WeeklyActionsSchema, type WeeklyActions } from './schemas';
import { resolveModel, type AIConfig } from './provider';

const INSTRUCTIONS = `You are a strategic project manager.
The user will give you a big, vague goal. Break it down into 1 to 5 concrete weekly actions.
Rules:
- Actions must be doable in a single sitting (15 to 180 minutes).
- Use imperative verbs ("Draft", "Research", "Build"), not vague concepts ("Understand").
- Assign a mode-of-work tag (deep-work, admin, comms, learning, etc.).
- The advice must be one sentence explaining the best sequence.`;

export async function decomposeGoal(goal: string, ai: AIConfig): Promise<WeeklyActions> {
  const { object } = await generateObject({
    model: resolveModel(ai),
    schema: WeeklyActionsSchema,
    instructions: INSTRUCTIONS,
    prompt: goal,
    temperature: 0.4,
  });
  return object;
}