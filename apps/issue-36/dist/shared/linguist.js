const VOWELS = new Set(['a', 'e', 'i', 'o', 'u']);

export function normalizeWord(input) {
  if (!input) return '';
  let word = input.trim();
  word = word.replace(/^[^\p{L}']+|[^\p{L}']+$/gu, '');
  if (!word) return '';

  const original = word;
  const lower = word.toLowerCase();

  if (lower.endsWith('ing') && lower.length > 5) {
    let base = lower.slice(0, -3);
    if (base.length >= 2 && base.slice(-1) === base.slice(-2, -1) && !VOWELS.has(base.slice(-1))) {
      base = base.slice(0, -1);
    }
    if (!base.endsWith('e') && /[atiz]$/.test(base)) {
      base += 'e';
    }
    return base;
  }

  if (lower.endsWith('ed') && lower.length > 4) {
    let base = lower.slice(0, -2);
    if (base.endsWith('i')) {
      base = base.slice(0, -1) + 'y';
    }
    if (base.length >= 2 && base.slice(-1) === base.slice(-2, -1) && !VOWELS.has(base.slice(-1))) {
      base = base.slice(0, -1);
    }
    return base;
  }

  if (lower.endsWith('ies') && lower.length > 4) {
    return lower.slice(0, -3) + 'y';
  }

  if (lower.endsWith('s') && lower.length > 3 && !lower.endsWith('ss')) {
    return lower.slice(0, -1);
  }

  return /^[A-Z]/.test(original) ? original : lower;
}

export function inferGrammar(word) {
  if (!word) return 'Unknown';
  const lower = word.toLowerCase();
  if (/ing$/.test(lower)) return 'Verb (Present Participle)';
  if (/ed$/.test(lower)) return 'Verb (Past Tense)';
  if (/ly$/.test(lower)) return 'Adverb';
  if (/ous$|ful$|able$|ive$|al$|ic$/.test(lower)) return 'Adjective';
  if (/tion$|ment$|ness$|ity$|ship$|age$/.test(lower)) return 'Noun';
  if (/^[A-Z]/.test(word)) return 'Proper Noun';
  return 'Unknown';
}

export function endsSentence(text) {
  if (!text) return false;
  return /[.!?]\s*$/.test(text.trim());
}

export function mergeContext(previous, current) {
  if (!previous) return current || '';
  if (!current) return previous || '';
  const prevTrim = previous.trim();
  const currTrim = current.trim();
  if (!prevTrim) return currTrim;
  if (!currTrim) return prevTrim;

  if (!endsSentence(prevTrim)) {
    return `${prevTrim} ${currTrim}`.replace(/\s+/g, ' ').trim();
  }
  return currTrim;
}
