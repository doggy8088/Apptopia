import { Note } from "./types";
import { normalizeKey, toPosixPath } from "./utils";

export type TopicMode = "tag" | "folder" | "keyword";

export interface TopicFilter {
  mode: TopicMode;
  value: string;
}

export function parseTopic(topic: string): TopicFilter {
  const trimmed = topic.trim();
  const lower = trimmed.toLowerCase();

  if (lower.startsWith("tag:")) {
    return { mode: "tag", value: normalizeKey(trimmed.slice(4)) };
  }

  if (lower.startsWith("folder:")) {
    return { mode: "folder", value: normalizeKey(trimmed.slice(7)) };
  }

  if (lower.startsWith("keyword:")) {
    return { mode: "keyword", value: normalizeKey(trimmed.slice(8)) };
  }

  if (trimmed.startsWith("#")) {
    return { mode: "tag", value: normalizeKey(trimmed.slice(1)) };
  }

  if (trimmed.includes("/") || trimmed.includes("\\")) {
    return { mode: "folder", value: normalizeKey(trimmed.replace(/^[.\/]+/, "")) };
  }

  return { mode: "keyword", value: normalizeKey(trimmed) };
}

export function filterNotes(notes: Note[], topic: string): { filtered: Note[]; filter: TopicFilter } {
  const filter = parseTopic(topic);

  switch (filter.mode) {
    case "tag":
      return {
        filter,
        filtered: notes.filter((note) => note.tags.includes(filter.value))
      };
    case "folder":
      return {
        filter,
        filtered: notes.filter((note) => matchFolder(note, filter.value))
      };
    default:
      return {
        filter,
        filtered: notes.filter((note) => matchKeyword(note, filter.value))
      };
  }
}

function matchFolder(note: Note, folder: string): boolean {
  if (!folder) {
    return false;
  }
  const normalizedFolder = normalizeKey(toPosixPath(folder)).replace(/\/+$/, "");
  const normalizedPath = normalizeKey(toPosixPath(note.relativePath));
  return normalizedPath === normalizedFolder || normalizedPath.startsWith(`${normalizedFolder}/`);
}

function matchKeyword(note: Note, keyword: string): boolean {
  if (!keyword) {
    return false;
  }
  const haystack = `${note.title}\n${note.body}`.toLowerCase();
  return haystack.includes(keyword);
}
