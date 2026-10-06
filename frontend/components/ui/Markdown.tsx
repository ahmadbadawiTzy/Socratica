import React from "react";
import { cn } from "@/lib/cn";

const SAFE_URL = /^(https?:\/\/|mailto:|\/|#)/i;

function renderInline(text: string, keyPrefix: string): React.ReactNode[] {
  const out: React.ReactNode[] = [];
  const pattern = /(`[^`]+`)|(\*\*[\s\S]+?\*\*)|(\*[^*\n]+\*)|(\[([^\]]+)\]\(([^)\s]+)\))/g;
  let last = 0;
  let i = 0;
  let m: RegExpExecArray | null;

  while ((m = pattern.exec(text)) !== null) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const key = `${keyPrefix}-${i++}`;
    if (m[1] !== undefined) {
      out.push(<code key={key}>{m[1].slice(1, -1)}</code>);
    } else if (m[2] !== undefined) {
      out.push(<strong key={key}>{renderInline(m[2].slice(2, -2), key)}</strong>);
    } else if (m[3] !== undefined) {
      out.push(<em key={key}>{renderInline(m[3].slice(1, -1), key)}</em>);
    } else if (m[4] !== undefined) {
      const label = m[5];
      const url = m[6];
      if (SAFE_URL.test(url)) {
        const external = /^https?:/i.test(url);
        out.push(
          <a
            key={key}
            href={url}
            {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
          >
            {renderInline(label, key)}
          </a>
        );
      } else {
        out.push(<span key={key}>{label}</span>);
      }
    }
    last = pattern.lastIndex;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

function isSpecialLine(line: string): boolean {
  return (
    /^```/.test(line) ||
    /^#{1,6}\s+/.test(line) ||
    /^\s*[-*+]\s+/.test(line) ||
    /^\s*\d+[.)]\s+/.test(line) ||
    /^\s*>/.test(line) ||
    /^\s*(-{3,}|\*{3,}|_{3,})\s*$/.test(line)
  );
}

function renderBlocks(src: string): React.ReactNode[] {
  const lines = src.replace(/\r\n?/g, "\n").split("\n");
  const nodes: React.ReactNode[] = [];
  let i = 0;
  let key = 0;

  const push = (node: React.ReactNode) => {
    nodes.push(<React.Fragment key={key++}>{node}</React.Fragment>);
  };

  while (i < lines.length) {
    const line = lines[i];

    if (/^\s*$/.test(line)) {
      i++;
      continue;
    }

    if (/^```/.test(line)) {
      const lang = line.slice(3).trim();
      const buf: string[] = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i])) buf.push(lines[i++]);
      i++;
      const code = buf.join("\n");
      push(
        <pre>
          <code data-lang={lang || undefined}>{code}</code>
        </pre>
      );
      continue;
    }

    const heading = /^(#{1,6})\s+(.*)$/.exec(line);
    if (heading) {
      const level = Math.min(heading[1].length, 3);
      const content = heading[2];
      const cls = "font-semibold tracking-[-.03em] leading-snug";
      if (level <= 1) {
        push(<h2 className={cn("text-[1.3em]", cls)}>{renderInline(content, `h${key}`)}</h2>);
      } else if (level === 2) {
        push(<h3 className={cn("text-[1.15em]", cls)}>{renderInline(content, `h${key}`)}</h3>);
      } else {
        push(<h4 className={cn("text-[1.04em]", cls)}>{renderInline(content, `h${key}`)}</h4>);
      }
      i++;
      continue;
    }

    if (/^\s*(-{3,}|\*{3,}|_{3,})\s*$/.test(line)) {
      push(<hr />);
      i++;
      continue;
    }

    if (/^\s*>/.test(line)) {
      const buf: string[] = [];
      while (i < lines.length && /^\s*>/.test(lines[i])) {
        buf.push(lines[i].replace(/^\s*>\s?/, ""));
        i++;
      }
      push(<blockquote>{renderInline(buf.join(" "), `q${key}`)}</blockquote>);
      continue;
    }

    if (/^\s*[-*+]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*+]\s+/, ""));
        i++;
      }
      push(
        <ul>
          {items.map((item, idx) => (
            <li key={idx}>{renderInline(item, `ul${key}-${idx}`)}</li>
          ))}
        </ul>
      );
      continue;
    }

    if (/^\s*\d+[.)]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*\d+[.)]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+[.)]\s+/, ""));
        i++;
      }
      push(
        <ol>
          {items.map((item, idx) => (
            <li key={idx}>{renderInline(item, `ol${key}-${idx}`)}</li>
          ))}
        </ol>
      );
      continue;
    }

    const buf: string[] = [];
    while (i < lines.length && !/^\s*$/.test(lines[i]) && !isSpecialLine(lines[i])) {
      buf.push(lines[i]);
      i++;
    }
    push(<p className="whitespace-pre-line">{renderInline(buf.join("\n"), `p${key}`)}</p>);
  }

  return nodes;
}

export default function Markdown({ text, className }: { text: string; className?: string }) {
  return <div className={cn("md", className)}>{renderBlocks(text)}</div>;
}
