export type OutputFormat = "markdown";

export interface Note {
  id: string;
  title: string;
  path: string;
  relativePath: string;
  body: string;
  frontmatter: Record<string, unknown>;
  tags: string[];
  links: string[];
  embeds: string[];
  aliases: string[];
}

export interface BookChapter {
  title: string;
  notes?: string[];
  auto?: boolean;
}

export interface BookConfig {
  meta?: {
    title?: string;
    author?: string;
    language?: string;
  };
  source?: {
    vault?: string;
    topic?: string;
    tags?: string[];
    folders?: string[];
    keywords?: string[];
  };
  structure?: {
    chapters?: BookChapter[];
  };
  output?: {
    format?: OutputFormat;
    cover?: string;
    template?: string;
  };
}

export interface AssetRef {
  sourcePath: string;
  outputRelativePath: string;
}

export interface RenderResult {
  markdown: string;
  assets: AssetRef[];
  warnings: string[];
}

export interface ReporterIO {
  stdout: (message: string) => void;
  stderr: (message: string) => void;
}
