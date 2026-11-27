import { decomposeGoal } from '@/lib/ai/goal';
import { redact } from '@/lib/ai/provider';
import type { AIConfig } from '@/lib/ai/provider';

export async function POST(req: Request) {
  const { goal, ai } = (await req.json()) as { goal?: string; ai?: AIConfig };
  if (!goal?.trim()) return Response.json({ error: 'Goal cannot be empty.' }, { status: 400 });
  if (!ai) return Response.json({ error: 'Missing AI config.' }, { status: 400 });

  try {
    const result = await decomposeGoal(goal, ai);
    return Response.json({ result });
  } catch (err) {
    console.error('[goal]', redact(err));
    return Response.json({ error: redact(err) }, { status: 502 });
  }
}