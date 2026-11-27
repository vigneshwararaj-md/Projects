import type { Task } from '@/lib/types';
import type { Schedule } from '@/lib/scheduler';
import type { AIConfig } from '@/lib/ai/provider';
import { reviewDay } from '@/lib/ai/review';
import { redact } from '@/lib/ai/provider';

export const maxDuration = 30;

export async function POST(req: Request) {
  const { tasks = [], plan, ai, date } = (await req.json()) as {
    tasks?: Task[]; plan?: Schedule; ai?: AIConfig; date?: string;
  };
  if (!plan || !ai) return Response.json({ error: 'Plan required for review.' }, { status: 400 });

  const plannedIds = new Set(
    plan.blocks.filter(b => b.type === 'task').map(b => (b as { id: string }).id)
  );
  
  const planned = tasks.filter(t => plannedIds.has(t.id));
  const completed = planned.filter(t => t.done);
  const slipped = planned.filter(t => !t.done);
  const notPlanned = tasks.filter(t => !plannedIds.has(t.id) && !t.done);

  const slim = (t: Task) => ({
    id: t.id, title: t.title, priority: t.priority, estimateMin: t.estimateMin, tag: t.tag,
  });

  try {
    const review = await reviewDay({
      date: date ?? new Date().toISOString().slice(0, 10),
      availableMin: plan.availableMin,
      plannedMin: plan.plannedMin,
      completed: completed.map(slim),
      slipped: slipped.map(slim),
      notPlanned: notPlanned.map(slim),
    }, ai);

    return Response.json({ review });
  } catch (err) {
    console.error('[review]', redact(err));
    return Response.json({ error: redact(err) }, { status: 502 });
  }
}