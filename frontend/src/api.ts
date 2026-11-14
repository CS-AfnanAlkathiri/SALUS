import type { components } from './schema';
export type Schemas = components['schemas'];
const base = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(base + path, body === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(typeof data.detail === 'string' ? data.detail : 'SALUS could not complete this request. Please try again.');
  }
  return response.json();
}

export const readings: Record<string, [string, string]> = {
  resting_hr_bpm: ['Resting heart rate', 'bpm'],
  sleep_hours: ['Sleep duration', 'h'],
  systolic_bp_mmhg: ['Systolic pressure', 'mmHg'],
  diastolic_bp_mmhg: ['Diastolic pressure', 'mmHg'],
  body_temp_c: ['Body temperature', '°C'],
  fatigue_score_0_10: ['Fatigue', '/10'],
  headache_score_0_10: ['Headache', '/10'],
};

export const format = (number?: number | null) => number == null ? '—' :
  number.toLocaleString('en', { maximumFractionDigits: 2 });
