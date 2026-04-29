import { readFileSync } from 'node:fs';
import path from 'node:path';

export type CategoryKey = 'inflacao' | 'juros' | 'correcao_monetaria';

export type Frequency = 'monthly' | 'daily';

export interface IndicatorLatest {
  reference_date: string;
  value: number;
  ytd: number | null;
  last_12m: number | null;
  last_24m?: number | null;
}

export interface IndicatorSummary {
  code: string;
  slug: string;
  name: string;
  category: CategoryKey;
  frequency: Frequency;
  latest: IndicatorLatest;
}

export interface CategorySection {
  label: string;
  indicators: string[];
}

export interface IndicatorIndex {
  generated_at: string;
  categories: Record<CategoryKey, CategorySection>;
  indicators: IndicatorSummary[];
}

export interface IndicatorValue {
  reference_date: string;
  value: number;
  ytd: number | null;
  last_12m: number | null;
  last_24m: number | null;
  since_inception: number | null;
}

export interface IndicatorDetail {
  code: string;
  slug: string;
  name: string;
  short_description: string;
  long_description: string;
  category: CategoryKey;
  unit: 'percent' | string;
  frequency: Frequency;
  source: { name: string; url: string };
  meta: { title: string; description: string };
  latest: IndicatorLatest;
  values: IndicatorValue[];
  charts: { current_year: string; history: string };
  last_built_at: string;
}

const DATA_DIR = path.resolve('./data');

function readJson<T>(file: string): T {
  return JSON.parse(readFileSync(path.join(DATA_DIR, file), 'utf-8')) as T;
}

export function loadIndex(): IndicatorIndex {
  return readJson<IndicatorIndex>('indicators.json');
}

export function loadDetail(slug: string): IndicatorDetail {
  return readJson<IndicatorDetail>(`${slug}.json`);
}
