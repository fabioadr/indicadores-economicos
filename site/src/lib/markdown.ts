/**
 * Parser minimal para o long_description dos indicadores.
 * Cobre apenas o que aparece nos JSONs:
 *   - "## Heading"
 *   - parágrafos separados por linha em branco
 *   - listas com "- "
 *   - **bold** dentro de texto
 * Faz escape de HTML antes de aplicar a sintaxe — não aceita HTML literal.
 */

function escape(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function inline(text: string): string {
  return escape(text).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
}

export function renderMarkdown(src: string): string {
  const blocks = src.replace(/\r\n/g, '\n').split(/\n{2,}/);
  const html: string[] = [];

  for (const block of blocks) {
    const trimmed = block.trim();
    if (!trimmed) continue;

    if (trimmed.startsWith('## ')) {
      html.push(`<h2>${inline(trimmed.slice(3).trim())}</h2>`);
      continue;
    }

    const lines = trimmed.split('\n').map((l) => l.trim());
    if (lines.every((l) => l.startsWith('- '))) {
      const items = lines.map((l) => `<li>${inline(l.slice(2))}</li>`).join('');
      html.push(`<ul>${items}</ul>`);
      continue;
    }

    html.push(`<p>${inline(trimmed.replace(/\n/g, ' '))}</p>`);
  }

  return html.join('\n');
}
