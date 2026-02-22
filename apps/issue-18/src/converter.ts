import path from "node:path";
import { NoteIndex, resolveNoteTarget } from "./graph";
import { AssetRef, Note, RenderResult } from "./types";
import { isImageFile, slugify, toPosixPath } from "./utils";

interface ConverterContext {
  vaultPath: string;
  index: NoteIndex;
}

const CALLOUT_MAP: Record<string, { label: string; emoji: string }> = {
  note: { label: "Note", emoji: "📝" },
  warning: { label: "Warning", emoji: "⚠️" },
  tip: { label: "Tip", emoji: "💡" },
  info: { label: "Info", emoji: "ℹ️" },
  important: { label: "Important", emoji: "❗" },
  caution: { label: "Caution", emoji: "🚧" },
  danger: { label: "Danger", emoji: "🛑" }
};

export function renderNote(note: Note, context: ConverterContext, stack: Set<string> = new Set()): RenderResult {
  const warnings: string[] = [];
  const assets: AssetRef[] = [];

  if (stack.has(note.id)) {
    return {
      markdown: `> [Embedded note skipped: ${note.title}]`,
      assets,
      warnings: [`Detected embed cycle at ${note.id}`]
    };
  }

  const nextStack = new Set(stack);
  nextStack.add(note.id);

  let content = note.body;

  content = content.replace(/!\[\[([^\]]+)\]\]/g, (match, inner: string) => {
    const target = inner.split("|")[0].trim();
    const cleaned = target.split("#")[0].trim();

    if (!cleaned) {
      return match;
    }

    if (isImageFile(cleaned)) {
      const safeRelative = sanitizeRelativePath(cleaned);
      if (!safeRelative) {
        warnings.push(`Skipped unsafe asset path: ${cleaned}`);
        return `> [Skipped unsafe asset: ${cleaned}]`;
      }
      const assetPath = path.resolve(context.vaultPath, safeRelative);
      const outputRelativePath = toPosixPath(safeRelative);
      assets.push({ sourcePath: assetPath, outputRelativePath: path.posix.join("assets", outputRelativePath) });
      const altText = path.basename(cleaned, path.extname(cleaned));
      return `![${altText}](./assets/${outputRelativePath})`;
    }

    const targetNote = resolveNoteTarget(cleaned, context.index);
    if (!targetNote) {
      warnings.push(`Embed target not found: ${cleaned}`);
      return `> [Missing embedded note: ${cleaned}]`;
    }

    const embedded = renderNote(targetNote, context, nextStack);
    assets.push(...embedded.assets);
    warnings.push(...embedded.warnings);

    return `\n${embedded.markdown}\n`;
  });

  content = convertCallouts(content);
  content = convertWikilinks(content, context.index);
  content = stripInlineTags(content);

  return {
    markdown: content.trim(),
    assets,
    warnings
  };
}

function convertWikilinks(content: string, index: NoteIndex): string {
  return content.replace(/\[\[([^\]]+)\]\]/g, (match, inner: string, offset: number) => {
    if (offset > 0 && content[offset - 1] === "!") {
      return match;
    }

    const [targetRaw, aliasRaw] = inner.split("|");
    const target = targetRaw?.split("#")[0].trim() ?? "";
    const display = (aliasRaw ?? targetRaw).split("#")[0].trim();

    if (!target) {
      return display || match;
    }

    const note = resolveNoteTarget(target, index);
    if (!note) {
      return display || target;
    }

    const anchor = slugify(note.title);
    const text = display || note.title;
    return `[${text}](#${anchor})`;
  });
}

function convertCallouts(content: string): string {
  const lines = content.split(/\r?\n/);
  const converted = lines.map((line) => {
    const match = line.match(/^>\s*\[!(\w+)\]\s*(.*)$/);
    if (!match) {
      return line;
    }
    const type = match[1].toLowerCase();
    const title = match[2]?.trim();
    const mapping = CALLOUT_MAP[type] ?? { label: type.toUpperCase(), emoji: "💬" };
    const header = title ? `${mapping.emoji} ${mapping.label}: ${title}` : `${mapping.emoji} ${mapping.label}`;
    return `> **${header}**`;
  });

  return converted.join("\n");
}

function stripInlineTags(content: string): string {
  return content.replace(/(^|\s)#([A-Za-z0-9_-]+)/g, "$1$2");
}

function sanitizeRelativePath(inputPath: string): string | null {
  const trimmed = inputPath.replace(/\0/g, "").trim();
  if (!trimmed) {
    return null;
  }
  if (path.isAbsolute(trimmed)) {
    return null;
  }
  if (/^[A-Za-z]:[\\/]/.test(trimmed) || /^\\\\/.test(trimmed)) {
    return null;
  }
  const normalized = path.normalize(trimmed).replace(/^([./\\])+/, "");
  const segments = normalized.split(/[\\/]+/).filter(Boolean);
  if (segments.length === 0 || segments.some((segment) => segment === "..")) {
    return null;
  }
  return segments.join(path.sep);
}
