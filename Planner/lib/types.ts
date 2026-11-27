import { z } from 'zod';

export const Priority = z.enum(['P0', 'P1', 'P2', 'P3']);
export const Tag = z.enum(['deep-work', 'admin', 'comms', 'errand', 'learning', 'other']);

export const TaskSchema = z.object({
  id: z.string(),
  title: z.string(),
  priority: Priority,
  estimateMin: z.number().int().min(5).max(240),
  tag: Tag,
  deadline: z.string().nullable(),
  done: z.boolean(),
  plannedFor: z.string().nullable(),
  goalId: z.string().nullable(),
});
export type Task = z.infer<typeof TaskSchema>;