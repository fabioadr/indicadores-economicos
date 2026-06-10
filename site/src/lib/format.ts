import type { CategoryKey, IndicatorValue } from './data';

const MONTHS_PT = [
  'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
  'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
];

const MONTHS_PT_SHORT = [
  'jan', 'fev', 'mar', 'abr', 'mai', 'jun',
  'jul', 'ago', 'set', 'out', 'nov', 'dez',
];

function parseISO(iso: string): { year: number; month: number; day: number } {
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number);
  return { year: y, month: m, day: d };
}

export function formatPercent(n: number | null | undefined, fractionDigits = 2): string {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return `${n.toLocaleString('pt-BR', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })}%`;
}

export function formatMonthYear(iso: string): string {
  const { year, month } = parseISO(iso);
  return `${MONTHS_PT[month - 1]}/${year}`;
}

export function formatMonthShort(iso: string): string {
  const { month } = parseISO(iso);
  return MONTHS_PT_SHORT[month - 1];
}

export function formatDateLong(iso: string): string {
  const { year, month, day } = parseISO(iso);
  return `${day} de ${MONTHS_PT[month - 1]} de ${year}`;
}

export function formatDateShort(iso: string): string {
  const { year, month, day } = parseISO(iso);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(day)}/${pad(month)}/${year}`;
}

export function yearOf(iso: string): number {
  return parseISO(iso).year;
}

export function monthOf(iso: string): number {
  return parseISO(iso).month;
}

const CATEGORY_LABEL: Record<CategoryKey, string> = {
  inflacao: 'Inflação',
  juros: 'Juros',
  correcao_monetaria: 'Correção Monetária',
  construcao_civil: 'Construção Civil',
};

const CATEGORY_SLUG: Record<CategoryKey, string> = {
  inflacao: 'inflacao',
  juros: 'juros',
  correcao_monetaria: 'correcao-monetaria',
  construcao_civil: 'construcao-civil',
};

const SLUG_TO_CATEGORY: Record<string, CategoryKey> = {
  'inflacao': 'inflacao',
  'juros': 'juros',
  'correcao-monetaria': 'correcao_monetaria',
  'construcao-civil': 'construcao_civil',
};

export function categoryLabel(key: CategoryKey): string {
  return CATEGORY_LABEL[key];
}

export function categorySlug(key: CategoryKey): string {
  return CATEGORY_SLUG[key];
}

export function categoryFromSlug(slug: string): CategoryKey | undefined {
  return SLUG_TO_CATEGORY[slug];
}

/**
 * Reduz uma série diária para um valor por mês (último dia do mês com dado).
 * Para séries mensais, retorna os pontos como vieram (já são mensais).
 */
export function reduceToMonthly(values: IndicatorValue[]): IndicatorValue[] {
  if (values.length === 0) return values;
  const byMonth = new Map<string, IndicatorValue>();
  for (const v of values) {
    const { year, month } = parseISO(v.reference_date);
    const key = `${year}-${String(month).padStart(2, '0')}`;
    const prev = byMonth.get(key);
    if (!prev || v.reference_date > prev.reference_date) {
      byMonth.set(key, v);
    }
  }
  return Array.from(byMonth.values()).sort((a, b) =>
    a.reference_date.localeCompare(b.reference_date)
  );
}

export function groupByYearDesc(values: IndicatorValue[]): Array<{ year: number; values: IndicatorValue[] }> {
  const byYear = new Map<number, IndicatorValue[]>();
  for (const v of values) {
    const y = yearOf(v.reference_date);
    if (!byYear.has(y)) byYear.set(y, []);
    byYear.get(y)!.push(v);
  }
  return Array.from(byYear.entries())
    .sort((a, b) => b[0] - a[0])
    .map(([year, vs]) => ({ year, values: vs }));
}
