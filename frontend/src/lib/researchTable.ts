export type ParsedMarkdownTable = {
  headers: string[];
  rows: string[][];
};

export type MarkdownTableSegment =
  | { type: "markdown"; content: string }
  | { type: "table"; table: ParsedMarkdownTable };

export function parseMarkdownTable(content: string): ParsedMarkdownTable | null {
  const tableSegment = splitMarkdownTableSegments(content).find((segment) => segment.type === "table");
  return tableSegment?.type === "table" ? tableSegment.table : null;
}

export function splitMarkdownTableSegments(content: string): MarkdownTableSegment[] {
  const normalized = normalizeTableText(content);
  const lines = normalized
    .split("\n")
    .map((line) => line.trim());

  const segments: MarkdownTableSegment[] = [];
  let markdownBuffer: string[] = [];

  let index = 0;
  while (index < lines.length) {
    const header = parseTableRow(lines[index]);
    const separator = parseTableRow(lines[index + 1]);
    const startsTable = Boolean(header && separator && header.length >= 2 && isSeparatorRow(separator));

    if (!startsTable) {
      markdownBuffer.push(lines[index]);
      index += 1;
      continue;
    }

    if (markdownBuffer.some((line) => line.trim())) {
      segments.push({ type: "markdown", content: markdownBuffer.join("\n").trim() });
    }
    markdownBuffer = [];

    const rows: string[][] = [];
    index += 2;
    while (index < lines.length) {
      const line = lines[index];
      const row = parseTableRow(line);
      if (!row) break;
      if (isSeparatorRow(row)) {
        index += 1;
        continue;
      }
      rows.push(normalizeRowLength(row, header.length));
      index += 1;
    }

    if (rows.length > 0) {
      segments.push({ type: "table", table: { headers: header, rows } });
    } else {
      markdownBuffer.push(lines[index] ?? "");
      index += 1;
    }
  }

  if (markdownBuffer.some((line) => line.trim())) {
    segments.push({ type: "markdown", content: markdownBuffer.join("\n").trim() });
  }

  return segments.length ? segments : [{ type: "markdown", content }];
}

export function normalizeTableText(content: string): string {
  return content
    .replace(/\\n/g, "\n")
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .replace(/\s*\|\|\s*/g, "|\n|")
    .replace(/\|\s+\|(?=\s*(?:[:\-]{2,}|[A-Za-z0-9*_`]))/g, "|\n|")
    .replace(/^\s*[-*]\s+(?=\|)/gm, "");
}

function parseTableRow(line: string): string[] | null {
  const trimmed = line.trim();
  if (!trimmed.includes("|")) return null;

  const withEdges = trimmed.startsWith("|") ? trimmed : `|${trimmed}`;
  const bounded = withEdges.endsWith("|") ? withEdges : `${withEdges}|`;
  const cells = bounded
    .slice(1, -1)
    .split("|")
    .map((cell) => cleanCell(cell))
    .filter((cell, index, all) => cell || index < all.length - 1);

  return cells.length >= 2 ? cells : null;
}

function cleanCell(cell: string): string {
  return cell
    .trim()
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/\*(.+?)\*/g, "$1")
    .replace(/`(.+?)`/g, "$1");
}

function isSeparatorRow(cells: string[]): boolean {
  return cells.every((cell) => /^:?-{2,}:?$/.test(cell.replace(/\s/g, "")));
}

function normalizeRowLength(row: string[], length: number): string[] {
  if (row.length === length) return row;
  if (row.length < length) {
    return [...row, ...Array.from({ length: length - row.length }, () => "")];
  }
  return [...row.slice(0, length - 1), row.slice(length - 1).join(" | ")];
}
