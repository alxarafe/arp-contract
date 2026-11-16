import { EN } from './en.js';
import { ES } from './es.js';
import type { Language, TranslationCatalogues, TranslationKey } from './types.js';

const CATALOGUES: TranslationCatalogues = { es: ES, en: EN };

/** Spanish is the initial selection; English alone is the translation fallback. */
export function translate(
    language: Language,
    key: TranslationKey,
    catalogues: TranslationCatalogues = CATALOGUES,
    reportMissing?: (key: TranslationKey) => void,
): string {
    const text = catalogues[language][key] ?? catalogues.en[key];
    if (text !== undefined) return text;
    reportMissing?.(key);
    return `[i18n:${key}]`;
}