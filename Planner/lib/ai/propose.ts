import { generateObject } from 'ai';
import { PlanProposalSchema, type PlanProposal } from './schemas';
import { resolveModel, redact, type AIConfig } from './provider';
import type { Task } from '@/lib/types';

const INSTRUCTIONS = `You order a single day of work. You receive tasks with ids, the current time, the work window, lunch, and the available minutes.
Rules:
- Put P0 tasks in the first half of the day.
- Cluster tasks that use the same mode of work (same tag) to reduce context switching.
- Be realistic: if total estimate > available minutes, do NOT pretend it fits. Choose what must happen today and let the rest slip.
- mustDoToday: at most 3 ids, chosen from the input.
- Never invent ids. Every id must exist in the input.
- rationale: 1-2 sentences naming the key trade-off. No praise, no filler.
- risks: 0-3 short factual risks.`;

export type PlanInput = {
  date: string;
  currentTime: string;
  availableMin: number;
  workWindow: string;
  lunch: string;
  focusBlockMax: number;
  tasks: Array<Pick<Task, 'id' | 'title' | 'priority' | 'estimateMin' | 'tag' | 'deadline'>>;
};

export async function proposePlan(input: PlanInput, ai: AIConfig): Promise<PlanProposal | null> {
  try {
    const { object } = await generateObject({
      model: resolveModel(ai),
      schema: PlanProposalSchema,
      instructions: INSTRUCTIONS,
      prompt: JSON.stringify(input),
      temperature: 0.3,
    });
    return object;
  } catch (err) {
    console.error('[proposePlan] falling back to deterministic order:', redact(err));
    return null;
  }
}