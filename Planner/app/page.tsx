'use client';

import { useEffect, useMemo, useState } from 'react';
import type { Task } from '@/lib/types';
import type { Schedule, Settings } from '@/lib/scheduler';
import type { AIConfig } from '@/lib/ai/provider';
import type { ExtractedTask, PlanProposal, ReviewInsight, WeeklyActions } from '@/lib/ai/schemas';

const STORE = 'daily-plan-v1';

const DEFAULT_SETTINGS: Settings = {
  dayStart: '09:00', dayEnd: '18:00', lunchStart: '12:30', lunchEnd: '13:15', focusBlock: 90, breakMin: 15,
};

const DEFAULT_AI: AIConfig = { provider: 'groq', model: 'openai/gpt-oss-120b', apiKey: '' };

function today() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function generateId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
  return Math.random().toString(36).substring(2, 15);
}

export default function Page() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [plan, setPlan] = useState<Schedule | null>(null);
  const [proposal, setProposal] = useState<PlanProposal | null>(null);
  const [review, setReview] = useState<ReviewInsight | null>(null);

  const [dump, setDump] = useState('');
  const [manual, setManual] = useState('');
  const [goalInput, setGoalInput] = useState('');
  const [goalAdvice, setGoalAdvice] = useState<string | null>(null);

  const [ai, setAi] = useState<AIConfig>(DEFAULT_AI);
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);

  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // --- FOCUS TIMER STATE ---
  const [activeTask, setActiveTask] = useState<{ id: string, title: string } | null>(null);
  const [timeLeft, setTimeLeft] = useState<number>(0); // in seconds
  const [timerRunning, setTimerRunning] = useState<boolean>(false);

  useEffect(() => {
    const raw = localStorage.getItem(STORE);
    if (!raw) return;
    try {
      const s = JSON.parse(raw);
      setTasks(s.tasks ?? []);
      setPlan(s.plan ?? null);
      setReview(s.review ?? null);
      setAi(s.ai ?? DEFAULT_AI);
      setSettings(s.settings ?? DEFAULT_SETTINGS);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    localStorage.setItem(STORE, JSON.stringify({ tasks, plan, review, ai, settings }));
  }, [tasks, plan, review, ai, settings]);

  // --- TIMER LOGIC ---
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (timerRunning && timeLeft > 0) {
      interval = setInterval(() => setTimeLeft(t => t - 1), 1000);
    } else if (timeLeft === 0 && timerRunning) {
      setTimerRunning(false);
      // Optional: Play a sound here if you want
    }
    return () => clearInterval(interval);
  }, [timerRunning, timeLeft]);

  const startFocus = (id: string, title: string, mins: number) => {
    setActiveTask({ id, title });
    setTimeLeft(mins * 60);
    setTimerRunning(true);
  };

  const stopFocus = () => {
    setTimerRunning(false);
    setActiveTask(null);
    setTimeLeft(0);
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };
  // ---------------------

  const open = useMemo(() => tasks.filter(t => !t.done), [tasks]);

  async function call<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(path, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error ?? `Request failed (${res.status})`);
    return data as T;
  }

  async function run(name: string, fn: () => Promise<void>) {
    setBusy(name); setError(null); setNotice(null);
    try { await fn(); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(null); }
  }

  const extract = () => run('extract', async () => {
    const data = await call<{ tasks: ExtractedTask[] }>('/api/extract', { text: dump, ai });
    const added: Task[] = data.tasks.map(t => ({ ...t, id: generateId(), done: false, plannedFor: today(), goalId: null }));
    setTasks(prev => [...prev, ...added]);
    setDump('');
  });

  const breakDownGoal = () => run('goal', async () => {
    const data = await call<{ result: WeeklyActions }>('/api/goal', { goal: goalInput, ai });
    const added: Task[] = (data.result?.actions || []).map(t => ({ 
      ...t, id: generateId(), priority: 'P1', deadline: null, done: false, plannedFor: today(), goalId: null 
    }));
    setTasks(prev => [...prev, ...added]);
    setGoalAdvice(data.result?.advice || null);
    setGoalInput('');
  });

  const addManual = () => {
    const title = manual.trim();
    if (!title) return;
    setTasks(prev => [...prev, {
      id: generateId(), title, priority: 'P1', estimateMin: 30, tag: 'other', deadline: null, done: false, plannedFor: today(), goalId: null,
    }]);
    setManual('');
  };

  const planDay = () => run('plan', async () => {
    const data = await call<{ schedule: Schedule; proposal: PlanProposal | null }>('/api/plan', { tasks, settings, ai, date: today() });
    setPlan(data.schedule);
    setProposal(data.proposal);
    setReview(null);
    setNotice(data.proposal ? 'Plan generated with AI ordering.' : 'AI unavailable — used deterministic priority order.');
  });

  const reviewDay = () => run('review', async () => {
    if (!plan) throw new Error('Generate a plan first.');
    const data = await call<{ review: ReviewInsight }>('/api/review', { tasks, plan, ai, date: today() });
    setReview(data.review);
  });

  return (
    <>
      <main>
        <h1>Daily Plan</h1>
        <p className="sub">
          {open.length} open · {tasks.filter(t => t.done).length} done
          {plan ? ` · ${plan.plannedMin} planned / ${plan.availableMin} available min` : ''}
        </p>

        <section className="card">
          <h2>Brain dump</h2>
          <textarea value={dump} onChange={e => setDump(e.target.value)} placeholder="Everything on your mind. Messy is fine." />
          <div className="row" style={{ marginTop: 8 }}>
            <button onClick={extract} disabled={busy !== null || !dump.trim()}>
              {busy === 'extract' ? 'Extracting…' : 'Extract tasks'}
            </button>
          </div>
        </section>

        <section className="card">
          <h2>Weekly Goals</h2>
          <div className="row">
            <input value={goalInput} onChange={e => setGoalInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && breakDownGoal()} placeholder="e.g., Learn React basics" style={{ flex: 1 }} />
            <button onClick={breakDownGoal} disabled={busy !== null || !goalInput.trim()}>
              {busy === 'goal' ? 'Breaking down…' : 'Break into actions'}
            </button>
          </div>
          {goalAdvice && <p className="sub" style={{ marginTop: 10 }}><strong>Strategy:</strong> {goalAdvice}</p>}
        </section>

        <section className="card">
          <h2>Tasks</h2>
          <div className="row" style={{ marginBottom: 12 }}>
            <input value={manual} onChange={e => setManual(e.target.value)} onKeyDown={e => e.key === 'Enter' && addManual()} placeholder="Add a simple task manually" style={{ flex: 1 }} />
            <button className="ghost" onClick={addManual}>Add</button>
          </div>
          <ul>
            {tasks.map(t => (
              <li key={t.id} className={`task ${t.done ? 'done' : ''}`}>
                <input type="checkbox" checked={t.done} onChange={() => setTasks(prev => prev.map(x => x.id === t.id ? { ...x, done: !x.done } : x))} />
                <span className="pill">{t.priority}</span>
                <span className="pill">{t.estimateMin}m</span>
                <span style={{ flex: 1 }}>{t.title}</span>
                <span className="pill">{t.tag}</span>
              </li>
            ))}
            {tasks.length === 0 && <li className="sub">No tasks yet.</li>}
          </ul>
          <div className="row" style={{ marginTop: 12 }}>
            <button onClick={planDay} disabled={busy !== null || open.length === 0}>
              {busy === 'plan' ? 'Planning…' : 'Plan my day'}
            </button>
            <button className="ghost" onClick={reviewDay} disabled={busy !== null || !plan}>
              {busy === 'review' ? 'Reviewing…' : 'Review my day'}
            </button>
          </div>
        </section>

        {plan && (
          <section className="card">
            <h2>Schedule</h2>
            {proposal?.rationale && <p className="sub">{proposal.rationale}</p>}
            {plan.blocks.map((b, i) => (
              <div key={i} className={`block ${b.type}`}>
                <span className="time">{b.label}</span>
                {b.type === 'task' ? (
                  <>
                    <span className="pill">{b.priority}</span>
                    <span style={{ flex: 1 }}>{b.title}</span>
                    <span className="pill">{b.tag}</span>
                    <button 
                      className="ghost" 
                      style={{ padding: '4px 8px', fontSize: '12px', marginLeft: '8px' }}
                      onClick={() => startFocus(b.id, b.title, b.end - b.start)}
                    >
                      Focus
                    </button>
                  </>
                ) : (
                  <span>{b.type === 'lunch' ? 'Lunch' : 'Break'}</span>
                )}
              </div>
            ))}
            {plan.unscheduled.length > 0 && (
              <>
                <h3>Will not fit today ({plan.unscheduled.length})</h3>
                <ul>
                  {plan.unscheduled.map(u => <li key={u.id} className="sub">{u.title} — {u.remainingMin} min remaining</li>)}
                </ul>
              </>
            )}
          </section>
        )}

        {review && (
          <section className="card">
            <h2>Review</h2>
            <p><strong>{review.headline}</strong></p>
            {review.patterns.map((p, i) => (
              <p key={i} className="sub"><strong>{p.pattern}</strong> — {p.evidence}</p>
            ))}
            <p>Tomorrow: {review.oneChange}</p>
          </section>
        )}

        <section className="card">
          <details>
            <summary>AI settings (BYOK)</summary>
            <div className="row" style={{ marginTop: 10 }}>
              <input
                type="password"
                value={ai.apiKey ?? ''}
                onChange={e => setAi({ ...ai, apiKey: e.target.value })}
                placeholder="gsk_… (stored in this browser only)"
                style={{ flex: 1 }}
              />
              <button className="ghost" onClick={() => setAi({ ...ai, apiKey: '' })}>Clear key</button>
            </div>
          </details>
        </section>

        {error && <p className="err">{error}</p>}
        {notice && <p className="notice">{notice}</p>}
      </main>

      {/* STICKY FOCUS BAR */}
      {activeTask && (
        <div style={{
          position: 'fixed', bottom: 0, left: 0, right: 0, 
          background: '#121519', borderTop: '1px solid #2f6fed', 
          padding: '16px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '20px',
          boxShadow: '0 -10px 30px rgba(0,0,0,0.5)', zIndex: 50
        }}>
          <div>
            <div className="sub" style={{ marginBottom: 4 }}>Currently Focusing On</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{activeTask.title}</div>
          </div>
          <div style={{ fontSize: '36px', fontVariantNumeric: 'tabular-nums', color: timerRunning ? '#2f6fed' : '#ff6b6b' }}>
            {formatTime(timeLeft)}
          </div>
          <div className="row">
            <button className="ghost" onClick={() => setTimerRunning(!timerRunning)}>
              {timerRunning ? 'Pause' : 'Resume'}
            </button>
            <button 
              onClick={() => {
                setTasks(prev => prev.map(x => x.id === activeTask.id ? { ...x, done: true } : x));
                stopFocus();
              }}
              style={{ background: '#2f6fed' }}
            >
              Complete Task
            </button>
            <button className="ghost" onClick={stopFocus}>Close</button>
          </div>
        </div>
      )}
    </>
  );
}