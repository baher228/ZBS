import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { ClipboardCopy } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { splitMarkdownTableSegments, type ParsedMarkdownTable } from "@/lib/researchTable";

export function ResearchDataBlock({ title, content }: { title: string; content: unknown }) {
  const [copied, setCopied] = useState(false);
  const label = title.replaceAll("_", " ");
  const displayContent = formatResearchValue(content);

  const copy = () => {
    navigator.clipboard.writeText(displayContent).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="border border-foreground/15 bg-card/40 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-foreground/10 bg-foreground/[0.03]">
        <span className="label-mono text-[10px] capitalize">{label}</span>
        <button
          onClick={copy}
          className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
        >
          <ClipboardCopy className="h-3 w-3" />
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <div className="px-4 py-3">
        <ResearchMarkdown content={displayContent} textClassName="text-xs" />
      </div>
    </div>
  );
}

export function ResearchMarkdown({
  content,
  textClassName = "text-sm",
}: {
  content: string;
  textClassName?: string;
}) {
  const segments = splitMarkdownTableSegments(content);

  return (
    <div className="space-y-3">
      {segments.map((segment, index) =>
        segment.type === "table" ? (
          <CompetitorTable key={index} table={segment.table} />
        ) : (
          <div key={index} className={`prose-chat leading-relaxed ${textClassName}`}>
            <ReactMarkdown>{segment.content}</ReactMarkdown>
          </div>
        ),
      )}
    </div>
  );
}

function CompetitorTable({ table }: { table: ParsedMarkdownTable }) {
  return (
    <div className="overflow-hidden border border-foreground/10 bg-background">
      <div className="overflow-x-auto">
        <Table className="min-w-[980px] table-fixed">
          <TableHeader className="bg-foreground/[0.06]">
            <TableRow className="hover:bg-transparent">
              {table.headers.map((header, index) => (
                <TableHead
                  key={`${header}-${index}`}
                  className="h-auto px-3 py-2 text-[10px] uppercase tracking-wider text-foreground/70"
                >
                  {header}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {table.rows.map((row, rowIndex) => (
              <TableRow key={rowIndex} className="hover:bg-primary/[0.03]">
                {table.headers.map((header, cellIndex) => (
                  <TableCell
                    key={`${header}-${rowIndex}-${cellIndex}`}
                    className="break-words px-3 py-3 text-[11px] leading-relaxed align-top text-foreground/80"
                  >
                    {row[cellIndex] || "-"}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

export function formatResearchValue(value: unknown): string {
  if (value == null) return "";
  if (typeof value === "string") {
    return value.includes("see embedded JSON above") ? "" : value;
  }
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) {
    return value
      .map((item) => (typeof item === "object" ? formatResearchValue(item) : `- ${formatResearchValue(item)}`))
      .filter(Boolean)
      .join("\n");
  }
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .map(([key, nested]) => {
        const formatted = formatResearchValue(nested);
        if (!formatted) return "";
        const label = key.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
        return typeof nested === "object" ? `### ${label}\n${formatted}` : `**${label}:** ${formatted}`;
      })
      .filter(Boolean)
      .join("\n\n");
  }
  return String(value);
}
