import type { EN } from './en.js';

export type Language = 'es' | 'en';
export type TranslationKey = keyof typeof EN;
export type TranslationCatalogue = Readonly<Partial<Record<TranslationKey, string>>>;
export type TranslationCatalogues = Readonly<Record<Language, TranslationCatalogue>>;