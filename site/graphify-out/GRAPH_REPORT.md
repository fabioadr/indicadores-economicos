# Graph Report - site  (2026-07-11)

## Corpus Check
- 4 files · ~45,128 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 27 nodes · 38 edges · 6 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]

## God Nodes (most connected - your core abstractions)
1. `parseISO()` - 8 edges
2. `readJson()` - 5 edges
3. `yearOf()` - 3 edges
4. `inline()` - 3 edges
5. `formatPercent()` - 2 edges
6. `formatValue()` - 2 edges
7. `formatMonthYear()` - 2 edges
8. `formatMonthShort()` - 2 edges
9. `formatDateLong()` - 2 edges
10. `formatDateShort()` - 2 edges

## Surprising Connections (you probably didn't know these)
- `formatDateLong()` --calls--> `parseISO()`  [EXTRACTED]
  src/lib/format.ts → src/lib/format.ts  _Bridges community 1 → community 0_
- `yearOf()` --calls--> `parseISO()`  [EXTRACTED]
  src/lib/format.ts → src/lib/format.ts  _Bridges community 1 → community 4_

## Communities

### Community 0 - "Community 0"
Cohesion: 0.33
Nodes (1): formatDateLong()

### Community 1 - "Community 1"
Cohesion: 0.33
Nodes (6): formatDateShort(), formatMonthShort(), formatMonthYear(), monthOf(), parseISO(), reduceToMonthly()

### Community 2 - "Community 2"
Cohesion: 0.6
Nodes (5): loadCalendar(), loadDetail(), loadGroups(), loadIndex(), readJson()

### Community 3 - "Community 3"
Cohesion: 0.83
Nodes (3): escape(), inline(), renderMarkdown()

### Community 4 - "Community 4"
Cohesion: 1.0
Nodes (2): groupByYearDesc(), yearOf()

### Community 5 - "Community 5"
Cohesion: 1.0
Nodes (2): formatPercent(), formatValue()

## Knowledge Gaps
- **Thin community `Community 0`** (6 nodes): `categoryFromSlug()`, `categoryLabel()`, `categorySlug()`, `formatDateLong()`, `isLevelUnit()`, `format.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 4`** (2 nodes): `groupByYearDesc()`, `yearOf()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 5`** (2 nodes): `formatPercent()`, `formatValue()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `parseISO()` connect `Community 1` to `Community 0`, `Community 4`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `yearOf()` connect `Community 4` to `Community 0`, `Community 1`?**
  _High betweenness centrality (0.002) - this node is a cross-community bridge._