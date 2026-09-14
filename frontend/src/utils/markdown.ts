/**
 * High-fidelity GitHub Flavored Markdown (GFM) to HTML parser.
 * Converts headings, tables, task lists, blockquotes, GitHub alerts, code blocks,
 * and inline styles into structured HTML ready for safe DOMPurify sanitization.
 */

export function parseMarkdownToHtml(markdown: string): string {
  if (!markdown) return '';

  let html = markdown;

  // 1. Normalize line endings
  html = html.replace(/\r\n/g, '\n');

  // 2. Code blocks (```lang ... ```) - escape and format
  html = html.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (_match, lang, code) => {
    const escapedCode = code
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    const langLabel = lang ? `<span class="code-lang-tag">${lang}</span>` : '';
    return `<div class="code-block-wrapper">${langLabel}<pre><code class="language-${lang || 'text'}">${escapedCode}</code></pre></div>`;
  });

  // 3. GitHub Alerts (> [!NOTE], > [!TIP], > [!IMPORTANT], > [!WARNING], > [!CAUTION])
  html = html.replace(
    /^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*\n((?:>.*(?:\n|$))*)/gim,
    (_match, type, content) => {
      const cleanContent = content.replace(/^>\s?/gm, '').trim();
      const alertType = type.toUpperCase();
      let colorClass = 'alert-note';
      let title = 'Note';

      if (alertType === 'TIP') {
        colorClass = 'alert-tip';
        title = 'Tip';
      } else if (alertType === 'IMPORTANT') {
        colorClass = 'alert-important';
        title = 'Important';
      } else if (alertType === 'WARNING') {
        colorClass = 'alert-warning';
        title = 'Warning';
      } else if (alertType === 'CAUTION') {
        colorClass = 'alert-caution';
        title = 'Caution';
      }

      return `<div class="github-alert ${colorClass}"><div class="github-alert-title">${title}</div><div class="github-alert-content">${cleanContent}</div></div>\n`;
    }
  );

  // 4. Tables (| Header | Header | ... |)
  html = html.replace(
    /(?:(?:^|\n)\|[^\n]+\|\r?\n\|[-: |]+\|\r?\n(?:\|[^\n]+\|\r?\n?)+)/g,
    (tableBlock) => {
      const lines = tableBlock.trim().split('\n').map((l) => l.trim());
      if (lines.length < 3) return tableBlock;

      const headerCols = lines[0].split('|').slice(1, -1).map((c) => c.trim());
      const bodyRows = lines.slice(2).map((l) => l.split('|').slice(1, -1).map((c) => c.trim()));

      let tableHtml = '<div class="table-container"><table class="markdown-table"><thead><tr>';
      headerCols.forEach((h) => {
        tableHtml += `<th>${h}</th>`;
      });
      tableHtml += '</tr></thead><tbody>';

      bodyRows.forEach((row) => {
        tableHtml += '<tr>';
        row.forEach((cell) => {
          tableHtml += `<td>${cell}</td>`;
        });
        tableHtml += '</tr>';
      });

      tableHtml += '</tbody></table></div>';
      return `\n${tableHtml}\n`;
    }
  );

  // 5. Task Lists (- [ ] / - [x])
  html = html.replace(
    /^-\s*\[([ xX])\]\s*(.+)$/gm,
    (_match, check, text) => {
      const isChecked = check.toLowerCase() === 'x';
      return `<li class="task-list-item"><input type="checkbox" disabled ${isChecked ? 'checked' : ''} class="task-checkbox" /> <span>${text}</span></li>`;
    }
  );

  // 6. Headers (# H1 to ###### H6)
  html = html.replace(/^######\s+(.+)$/gm, '<h6 class="md-h6">$1</h6>');
  html = html.replace(/^#####\s+(.+)$/gm, '<h5 class="md-h5">$1</h5>');
  html = html.replace(/^####\s+(.+)$/gm, '<h4 class="md-h4">$1</h4>');
  html = html.replace(/^###\s+(.+)$/gm, '<h3 class="md-h3">$1</h3>');
  html = html.replace(/^##\s+(.+)$/gm, '<h2 class="md-h2">$1</h2>');
  html = html.replace(/^#\s+(.+)$/gm, '<h1 class="md-h1">$1</h1>');

  // 7. Horizontal Rules (--- or ***)
  html = html.replace(/^(?:---|___|\*\*\*)\s*$/gm, '<hr class="md-hr" />');

  // 8. Blockquotes (> quote)
  html = html.replace(/^>\s*(.+)$/gm, '<blockquote class="md-blockquote">$1</blockquote>');

  // 9. Inline code (`code`)
  html = html.replace(/`([^`\n]+)`/g, '<code class="inline-code">$1</code>');

  // 10. Bold (**text** or __text__)
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>');

  // 11. Italic (*text* or _text_)
  html = html.replace(/(^|[^*])\*([^*]+)\*([^*]|$)/g, '$1<em>$2</em>$3');
  html = html.replace(/(^|[^_])_([^_]+)_([^_]|$)/g, '$1<em>$2</em>$3');

  // 12. Strikethrough (~~text~~)
  html = html.replace(/~~([^~]+)~~/g, '<del>$1</del>');

  // 13. Links ([text](url))
  html = html.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer" class="md-link">$1</a>'
  );

  // 14. Unordered list items (- text or * text)
  html = html.replace(/^[-*]\s+(?!\[[ xX]\])(.+)$/gm, '<li class="md-li">$1</li>');

  // 15. Ordered list items (1. text)
  html = html.replace(/^\d+\.\s+(.+)$/gm, '<li class="md-oli">$1</li>');

  // 16. Paragraphs: Wrap lines separated by blank lines that are not already blocks
  const blocks = html.split(/\n{2,}/);
  const formattedBlocks = blocks.map((block) => {
    const trimmed = block.trim();
    if (!trimmed) return '';
    if (
      trimmed.startsWith('<h1') ||
      trimmed.startsWith('<h2') ||
      trimmed.startsWith('<h3') ||
      trimmed.startsWith('<h4') ||
      trimmed.startsWith('<h5') ||
      trimmed.startsWith('<h6') ||
      trimmed.startsWith('<div') ||
      trimmed.startsWith('<table') ||
      trimmed.startsWith('<hr') ||
      trimmed.startsWith('<blockquote') ||
      trimmed.startsWith('<li')
    ) {
      return trimmed;
    }
    return `<p class="md-p">${trimmed.replace(/\n/g, '<br />')}</p>`;
  });

  return formattedBlocks.join('\n\n');
}
