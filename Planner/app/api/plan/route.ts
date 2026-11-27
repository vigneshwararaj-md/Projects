import type { Task } from '@/lib/types';
import { buildSchedule, availableMinutes, type Settings } from '@/lib/scheduler';
import { applyProposal } from '@/lib/plan/apply';
import { proposePlan } from '@/lib/ai/propose';
import type { AIConfig } from '@/lib/ai/provider';

export async function POST(req: Request) {
  const body = (await req.json()) as { tasks?: Task[]; settings?: Settings; ai?: AIConfig; date?: string };
  const { tasks = [], settings, ai, date } = body;
  if (!settings || !ai) return Response.json({ error: 'Missing settings or AI config.' }, { status: 400 });

  const open = tasks.filter(t => !t.done).slice(0, 60);
  if (open.length === 0) return Response.json({ schedule: buildSchedule([], settings), proposal: null, source: 'empty' });

  const now = new Date();
  const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

  const proposal = await proposePlan({
    date: date ?? new Date().toISOString().slice(0, 10),
    currentTime,
    availableMin: availableMinutes(settings),
    workWindow: `${settings.dayStart}–${settings.dayEnd}`,
    lunch: `${settings.lunchStart}–${settings.lunchEnd}`,
    focusBlockMax: settings.focusBlock,
    tasks: open.map(({ id, title, priority, estimateMin, tag, deadline }) => ({ id, title, priority, estimateMin, tag, deadline })),
  }, ai);

  const ordered = applyProposal(open, proposal);
  const schedule = buildSchedule(ordered, settings);

  return Response.json({ schedule, proposal, source: proposal ? 'llm' : 'deterministic' });
}