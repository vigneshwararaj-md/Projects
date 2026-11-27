import type { Task } from './types';

export type Settings = {
  dayStart: string; dayEnd: string;
  lunchStart: string; lunchEnd: string;
  focusBlock: number; breakMin: number;
};

type Base = { start: number; end: number; label: string };
export type Block =
  | (Base & { type: 'task'; id: string; title: string; tag: string; priority: string })
  | (Base & { type: 'break' | 'lunch' });

export type Schedule = {
  blocks: Block[];
  unscheduled: Array<{ id: string; title: string; remainingMin: number }>;
  plannedMin: number;
  availableMin: number;
};

export const toMin = (s: string) => {
  const [h, m] = s.split(':').map(Number);
  return h * 60 + m;
};
export const toClock = (m: number) =>
  `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;

const label = <T extends { start: number; end: number }>(b: T) =>
  ({ ...b, label: `${toClock(b.start)}–${toClock(b.end)}` });

export function availableMinutes(s: Settings): number {
  const lunch = Math.max(0, toMin(s.lunchEnd) - toMin(s.lunchStart));
  return Math.max(0, toMin(s.dayEnd) - toMin(s.dayStart) - lunch);
}

export function buildSchedule(tasks: Task[], s: Settings): Schedule {
  const start = toMin(s.dayStart), end = toMin(s.dayEnd);
  const lunchStart = toMin(s.lunchStart), lunchEnd = toMin(s.lunchEnd);

  const queue = tasks.filter(t => !t.done).map(t => ({ ...t, left: t.estimateMin }));
  const blocks: Block[] = [];
  let cursor = start, sinceBreak = 0, i = 0, lunchPlaced = false;

  while (cursor < end && i < queue.length) {
    if (!lunchPlaced) {
      if (cursor >= lunchStart && cursor < lunchEnd) {
        blocks.push(label({ type: 'lunch', start: lunchStart, end: lunchEnd }));
        cursor = lunchEnd; sinceBreak = 0; lunchPlaced = true; continue;
      }
      if (cursor >= lunchEnd) lunchPlaced = true;
    }

    if (sinceBreak >= s.focusBlock) {
      const bEnd = Math.min(cursor + s.breakMin, end);
      if (bEnd - cursor >= 5) blocks.push(label({ type: 'break', start: cursor, end: bEnd }));
      cursor = bEnd; sinceBreak = 0; continue;
    }

    const t = queue[i];
    let chunk = Math.min(t.left, s.focusBlock - sinceBreak, end - cursor);
    if (cursor < lunchStart && cursor + chunk > lunchStart) chunk = lunchStart - cursor;
    if (chunk < 5) { cursor += 5; continue; }

    blocks.push(label({
      type: 'task', id: t.id, title: t.title, tag: t.tag, priority: t.priority,
      start: cursor, end: cursor + chunk,
    }));
    cursor += chunk; t.left -= chunk; sinceBreak += chunk;
    if (t.left <= 0) i++;
  }

  const left = new Map(queue.map(t => [t.id, t.left]));
  const unscheduled = tasks
    .filter(t => !t.done && (left.get(t.id) ?? 0) > 0)
    .map(t => ({ id: t.id, title: t.title, remainingMin: left.get(t.id) ?? 0 }))
    .sort((a, b) => b.remainingMin - a.remainingMin);

  const plannedMin = blocks
    .filter((b): b is Extract<Block, { type: 'task' }> => b.type === 'task')
    .reduce((sum, b) => sum + (b.end - b.start), 0);

  return { blocks, unscheduled, plannedMin, availableMin: availableMinutes(s) };
}