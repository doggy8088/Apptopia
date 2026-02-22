import path from "node:path";
import { NoteIndex, resolveNoteTarget } from "./graph";
import { BookConfig, BookChapter, Note } from "./types";
import { normalizeKey, slugify } from "./utils";
import { TopicFilter } from "./filter";

export interface ChapterPlan {
  title: string;
  notes: Note[];
}

export interface BookPlan {
  chapters: ChapterPlan[];
  config: BookConfig;
  warnings: string[];
}

export function buildBookPlan(
  notes: Note[],
  ordered: Note[],
  index: NoteIndex,
  filter: TopicFilter,
  vaultPath: string,
  topic: string,
  config?: BookConfig
): BookPlan {
  const warnings: string[] = [];
  const planChapters: ChapterPlan[] = [];
  const remaining = new Set(ordered.map((note) => note.id));

  const configChapters = config?.structure?.chapters;

  if (configChapters && configChapters.length > 0) {
    for (const chapter of configChapters) {
      const chapterNotes: Note[] = [];
      const noteRefs = chapter.notes ?? [];
      for (const ref of noteRefs) {
        const note = resolveNoteTarget(ref, index);
        if (!note) {
          warnings.push(`book.yaml reference not found: ${ref}`);
          continue;
        }
        if (!remaining.has(note.id)) {
          continue;
        }
        remaining.delete(note.id);
        chapterNotes.push(note);
      }

      if (chapter.auto) {
        const autoNotes = ordered.filter((note) => remaining.has(note.id));
        for (const note of autoNotes) {
          remaining.delete(note.id);
        }
        chapterNotes.push(...autoNotes);
      }

      if (chapterNotes.length > 0) {
        planChapters.push({
          title: chapter.title || chapterNotes[0].title,
          notes: chapterNotes
        });
      }
    }
  }

  if (planChapters.length === 0) {
    for (const note of ordered) {
      planChapters.push({ title: note.title, notes: [note] });
    }
  }

  const fallbackTitle = path.basename(vaultPath) || "Obsidian Book";
  const title = config?.meta?.title ?? fallbackTitle;
  const author = config?.meta?.author ?? "";
  const language = config?.meta?.language ?? "zh-TW";

  const baseConfig: BookConfig = {
    meta: {
      title,
      author,
      language
    },
    source: {
      vault: vaultPath,
      topic
    },
    structure: {
      chapters: planChapters.map((chapter) => ({
        title: chapter.title,
        notes: chapter.notes.map((note) => note.id)
      }))
    },
    output: {
      format: "markdown"
    }
  };

  applyFilterMetadata(baseConfig, filter);

  return { chapters: planChapters, config: mergeConfig(baseConfig, config), warnings };
}

export function renderBookMarkdown(plan: ChapterPlan[], title: string, renderNote: (note: Note) => string): string {
  const sections: string[] = [];
  sections.push(`# ${title}`);

  for (const chapter of plan) {
    if (chapter.notes.length === 1 && chapter.title === chapter.notes[0].title) {
      const note = chapter.notes[0];
      sections.push(`\n## ${note.title}\n`);
      sections.push(renderNote(note));
      continue;
    }

    sections.push(`\n## ${chapter.title}\n`);
    for (const note of chapter.notes) {
      sections.push(`\n### ${note.title}\n`);
      sections.push(renderNote(note));
    }
  }

  return sections.join("\n").trim() + "\n";
}

function applyFilterMetadata(config: BookConfig, filter: TopicFilter): void {
  if (!config.source) {
    config.source = {};
  }
  switch (filter.mode) {
    case "tag":
      config.source.tags = [filter.value];
      break;
    case "folder":
      config.source.folders = [filter.value];
      break;
    case "keyword":
      config.source.keywords = [filter.value];
      break;
  }
}

function mergeConfig(base: BookConfig, provided?: BookConfig): BookConfig {
  if (!provided) {
    return base;
  }

  return {
    ...base,
    meta: {
      ...base.meta,
      ...provided.meta
    },
    source: {
      ...base.source,
      ...provided.source
    },
    structure: {
      ...base.structure,
      ...provided.structure
    },
    output: {
      ...base.output,
      ...provided.output
    }
  };
}

export function createAnchorMap(chapters: ChapterPlan[]): Map<string, string> {
  const map = new Map<string, string>();
  for (const chapter of chapters) {
    for (const note of chapter.notes) {
      map.set(normalizeKey(note.title), slugify(note.title));
    }
  }
  return map;
}

export function toBookChapters(chapters: ChapterPlan[]): BookChapter[] {
  return chapters.map((chapter) => ({
    title: chapter.title,
    notes: chapter.notes.map((note) => note.id)
  }));
}
