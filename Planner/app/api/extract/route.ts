import { extractTasks } from '@/lib/ai/extract';
import { redact } from '@/lib/ai/provider';
import type { AIConfig } from '@/lib/ai/provider';

export async function POST(req: Request) {
  const { text, ai } = (await req.json()) as { text?: string; ai?: AIConfig };
  if (!text?.trim()) return Response.json({ error: 'Nothing to extract.' }, { status: 400 });
  if (!ai) return Response.json({ error: 'Missing AI config.' }, { status: 400 });

  try {
    const tasks = await extractTasks(text, ai);
    return Response.json({ tasks });
  } catch (err) {
    console.error('[extract]', redact(err));
    return Response.json({ error: redact(err) }, { status: 502 });
  }
}