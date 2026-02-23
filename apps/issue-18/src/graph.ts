import { Note } from "./types";
import { normalizeKey } from "./utils";

export interface NoteIndex {
  byKey: Map<string, Note[]>;
}

export function createNoteIndex(notes: Note[]): NoteIndex {
  const byKey = new Map<string, Note[]>();

  for (const note of notes) {
    const keys = [note.id, note.title, ...note.aliases].map((key) => normalizeKey(key));
    for (const key of keys) {
      if (!key) {
        continue;
      }
      const existing = byKey.get(key);
      if (existing) {
        existing.push(note);
      } else {
        byKey.set(key, [note]);
      }
    }
  }

  return { byKey };
}

export function resolveNoteTarget(targetRaw: string, index: NoteIndex): Note | undefined {
  const target = normalizeKey(stripLinkDecorators(targetRaw));
  if (!target) {
    return undefined;
  }
  const matches = index.byKey.get(target);
  if (!matches || matches.length === 0) {
    return undefined;
  }
  return matches[0];
}

export function buildGraph(notes: Note[], index: NoteIndex): Map<string, Set<string>> {
  const graph = new Map<string, Set<string>>();

  for (const note of notes) {
    const edges = new Set<string>();
    for (const link of note.links) {
      const target = resolveNoteTarget(link, index);
      if (target && target.id !== note.id) {
        edges.add(target.id);
      }
    }
    graph.set(note.id, edges);
  }

  return graph;
}

export function orderNotes(notes: Note[], graph: Map<string, Set<string>>): { ordered: Note[]; hasCycle: boolean } {
  const noteMap = new Map(notes.map((note) => [note.id, note]));
  const inDegree = new Map<string, number>();

  for (const note of notes) {
    inDegree.set(note.id, 0);
  }

  for (const [source, targets] of graph.entries()) {
    if (!noteMap.has(source)) {
      continue;
    }
    for (const target of targets) {
      if (noteMap.has(target)) {
        inDegree.set(target, (inDegree.get(target) ?? 0) + 1);
      }
    }
  }

  const queue = notes
    .filter((note) => (inDegree.get(note.id) ?? 0) === 0)
    .sort((a, b) => a.title.localeCompare(b.title));

  const ordered: Note[] = [];

  while (queue.length > 0) {
    const current = queue.shift();
    if (!current) {
      continue;
    }
    ordered.push(current);
    const targets = graph.get(current.id);
    if (!targets) {
      continue;
    }
    for (const targetId of targets) {
      if (!inDegree.has(targetId)) {
        continue;
      }
      const nextDegree = (inDegree.get(targetId) ?? 0) - 1;
      inDegree.set(targetId, nextDegree);
      if (nextDegree === 0) {
        const target = noteMap.get(targetId);
        if (target) {
          queue.push(target);
          queue.sort((a, b) => a.title.localeCompare(b.title));
        }
      }
    }
  }

  if (ordered.length === notes.length) {
    return { ordered, hasCycle: false };
  }

  const fallback = [...notes].sort((a, b) => {
    const aDegree = inDegree.get(a.id) ?? 0;
    const bDegree = inDegree.get(b.id) ?? 0;
    if (aDegree !== bDegree) {
      return aDegree - bDegree;
    }
    return a.title.localeCompare(b.title);
  });

  return { ordered: fallback, hasCycle: true };
}

function stripLinkDecorators(raw: string): string {
  const withoutAlias = raw.split("|")[0];
  const withoutHeading = withoutAlias.split("#")[0];
  return withoutHeading.trim().replace(/\.md$/i, "");
}
