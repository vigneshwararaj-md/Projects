import type { Task } from '@/lib/types';
import type { PlanProposal } from '@/lib/ai/schemas';

const rank: Record<string, number> = { P0: 0, P1: 1, P2: 2, P3: 3 };

export const fallbackSort = (a: Task, b: Task) =>
  rank[a.priority] - rank[b.priority] ||
  a.tag.localeCompare(b.tag) ||
  a.estimateMin - b.estimateMin;

export function applyProposal(tasks: Task[], proposal: PlanProposal | null): Task[] {
  if (!proposal) return [...tasks].sort(fallbackSort);
  const byId = new Map(tasks.map(t => [t.id, t]));
  const seen = new Set<string>();
  const ordered: Task[] = [];
  for (const id of proposal.order) {
    const t = byId.get(id);
    if (t && !seen.has(id)) { ordered.push(t); seen.add(id); }
  }
  return [...ordered, ...tasks.filter(t => !seen.has(t.id)).sort(fallbackSort)];
}