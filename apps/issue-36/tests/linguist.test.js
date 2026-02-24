import assert from 'node:assert/strict';
import { test } from 'node:test';
import { inferGrammar, mergeContext, normalizeWord } from '../src/shared/linguist.js';

test('normalizeWord handles common inflections', () => {
  assert.equal(normalizeWord('disintegrating'), 'disintegrate');
  assert.equal(normalizeWord('running'), 'run');
  assert.equal(normalizeWord('studies'), 'study');
  assert.equal(normalizeWord('cats'), 'cat');
  assert.equal(normalizeWord('Soviet'), 'Soviet');
});

test('inferGrammar provides simple tags', () => {
  assert.equal(inferGrammar('disintegrating'), 'Verb (Present Participle)');
  assert.equal(inferGrammar('awkwardly'), 'Adverb');
  assert.equal(inferGrammar('Curiosity'), 'Noun');
});

test('mergeContext combines sentence fragments', () => {
  assert.equal(mergeContext('The Soviet Union was', 'disintegrating at that time.'),
    'The Soviet Union was disintegrating at that time.');
  assert.equal(mergeContext('It was an awkward moment.', 'Next line.'), 'Next line.');
});
