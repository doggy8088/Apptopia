import { describe, it, expect } from 'vitest';
import { extractUrl, validateUrl } from '../src/utils/validation';
import { isFileSizeAllowed } from '../src/utils/files';

describe('validation helpers', () => {
  it('extracts first url from text', () => {
    const text = 'Check this https://example.com/video and more';
    expect(extractUrl(text)).toBe('https://example.com/video');
  });

  it('returns null when no url is present', () => {
    expect(extractUrl('no link here')).toBeNull();
  });

  it('validates http/https URLs', () => {
    const result = validateUrl('https://example.com', 1000);
    expect(result.ok).toBe(true);
  });

  it('rejects non-http URLs', () => {
    const result = validateUrl('ftp://example.com', 1000);
    expect(result.ok).toBe(false);
  });

  it('rejects URLs exceeding length limit', () => {
    const longUrl = `https://example.com/${'a'.repeat(1005)}`;
    const result = validateUrl(longUrl, 1000);
    expect(result.ok).toBe(false);
  });

  it('checks file size limits', () => {
    expect(isFileSizeAllowed(100, 100)).toBe(true);
    expect(isFileSizeAllowed(101, 100)).toBe(false);
  });
});
