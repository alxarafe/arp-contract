import { test } from 'node:test';
import assert from 'node:assert/strict';
import { translate } from '../../out-unit/translate.js';
import { EN } from '../../out-unit/en.js';
import { ES } from '../../out-unit/es.js';

test('English reference covers declared translations and all reference keys resolve in both languages', () => {
    for (const key of Object.keys(ES)) assert.ok(Object.hasOwn(EN, key));
    for (const language of ['es', 'en']) {
        for (const key of Object.keys(EN)) {
            assert.ok(translate(language, key).length);
            assert.ok(!translate(language, key).startsWith('[i18n:'));
        }
    }
});

test('a missing Spanish translation falls back to English without reporting a reference error', () => {
    const reports = [];
    assert.equal(translate('es', 'heading.title', { es: {}, en: EN }, key => reports.push(key)), EN['heading.title']);
    assert.deepEqual(reports, []);
});

test('a key missing in both catalogues is identifiable and reported to the development hook', () => {
    const reports = [];
    for (const language of ['es', 'en']) {
        assert.equal(translate(language, 'heading.title', { es: {}, en: {} }, key => reports.push(key)),
            '[i18n:heading.title]');
    }
    assert.deepEqual(reports, ['heading.title', 'heading.title']);
});

test('English selection never silently falls back to Spanish if the reference is missing', () => {
    assert.equal(translate('en', 'heading.title', { es: ES, en: {} }), '[i18n:heading.title]');
});