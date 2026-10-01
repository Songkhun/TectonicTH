import test from 'node:test';
import assert from 'node:assert/strict';
import { initLang, getLang, setLang, onLangChange, t, field, I18N_STRINGS } from '../../src/i18n.js';

const memory = () => { const m = {}; return { getItem: k => m[k] ?? null, setItem: (k, v) => { m[k] = v; } }; };

test('defaults to Thai with no storage', () => {
  assert.equal(initLang(null), 'th');
});

test('throwing storage still loads in Thai and toggling works', () => {
  const bad = { getItem() { throw new Error('SecurityError'); }, setItem() { throw new Error('SecurityError'); } };
  assert.equal(initLang(bad), 'th');
  setLang('en');
  assert.equal(getLang(), 'en');
});

test('remembers language in storage', () => {
  const s = memory();
  initLang(s);
  setLang('en');
  assert.equal(initLang(s), 'en');
});

test('ignores unknown languages and notifies listeners', () => {
  initLang(null);
  let seen = null;
  onLangChange(l => { seen = l; });
  setLang('fr');
  assert.equal(getLang(), 'th');
  setLang('en');
  assert.equal(seen, 'en');
});

test('t falls back to the key for unknown strings', () => {
  initLang(null);
  assert.equal(t('no_such_key'), 'no_such_key');
});

test('every English key has a Thai string', () => {
  for (const k of Object.keys(I18N_STRINGS.en)) assert.ok(I18N_STRINGS.th[k], k);
});

test('field falls back to English when Thai is missing', () => {
  initLang(null);
  assert.equal(field({ title_en: 'Limestone' }, 'title'), 'Limestone');
  assert.equal(field({ title_th: 'หินปูน', title_en: 'Limestone' }, 'title'), 'หินปูน');
  assert.equal(field({}, 'title'), '');
});
