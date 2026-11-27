import { z } from 'zod';
import { Priority, Tag } from '@/lib/types';

export const ExtractedTaskSchema = z.object({
  title: z.string().describe('Imperative, <= 80 chars, no filler'),
  priority: Priority,
  estimateMin: z.number().int().min(5).max(240),
  tag: Tag,
  deadline: z.string().nullable().describe('YYYY-MM-DD or null'),
});
export const ExtractedTasksSchema = z.object({ tasks: z.array(ExtractedTaskSchema).max(30) });
export type ExtractedTask = z.infer<typeof ExtractedTaskSchema>;

export const PlanProposalSchema = z.object({
  order: z.array(z.string()).describe('Task ids, most important first'),
  groups: z.array(z.object({ label: z.string(), taskIds: z.array(z.string()) })).max(6),
  mustDoToday: z.array(z.string()).max(3),
  rationale: z.string().describe('1-2 sentences, name the trade-off, no praise'),
  risks: z.array(z.string()).max(3),
});
export type PlanProposal = z.infer<typeof PlanProposalSchema>;

export const ReviewInsightSchema = z.object({
  headline: z.string(),
  patterns: z.array(z.object({
    pattern: z.string(),
    evidence: z.string().describe('Cite specific task titles or numbers from the input'),
  })).max(3),
  oneChange: z.string().describe('One concrete, testable change for tomorrow'),
  suggestCarryOver: z.array(z.string()),
});
export type ReviewInsight = z.infer<typeof ReviewInsightSchema>;

export const WeeklyActionsSchema = z.object({
  actions: z.array(z.object({
    title: z.string().describe('Imperative verb, concrete action'),
    estimateMin: z.number().int().min(15).max(180),
    tag: Tag,
  })).min(1).max(5),
  advice: z.string().describe('One sentence of strategic advice on how to sequence these.'),
});
export type WeeklyActions = z.infer<typeof WeeklyActionsSchema>;
