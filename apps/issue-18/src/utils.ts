import path from "node:path";

export function normalizeKey(value: string): string {
  return value.trim().toLowerCase();
}

export function slugify(value: string): string {
  const cleaned = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");

  return cleaned || "note";
}

export function toPosixPath(value: string): string {
  return value.split(path.sep).join("/");
}

export function stripExtension(filename: string): string {
  return filename.replace(/\.[^.]+$/, "");
}

export function isImageFile(filename: string): boolean {
  return /\.(png|jpe?g|gif|svg|webp)$/i.test(filename);
}

export function uniqueStrings(values: string[]): string[] {
  return [...new Set(values)];
}

export function ensureTrailingSlash(value: string): string {
  return value.endsWith("/") ? value : `${value}/`;
}

export function isPathInside(basePath: string, targetPath: string): boolean {
  const relative = path.relative(basePath, targetPath);
  if (!relative) {
    return true;
  }
  return !relative.startsWith("..") && !path.isAbsolute(relative);
}
