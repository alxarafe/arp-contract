import { Injectable, effect, isDevMode, signal } from '@angular/core';
import { translate } from './translate.js';
import type { Language, TranslationKey } from './types.js';

const STORAGE_KEY = 'arp-demo.language';

function initialLanguage(): Language {
    try {
        return localStorage.getItem(STORAGE_KEY) === 'en' ? 'en' : 'es';
    } catch {
        return 'es';
    }
}

@Injectable({ providedIn: 'root' })
export class LanguageService {
    private readonly selection = signal<Language>(initialLanguage());
    private readonly reported = new Set<TranslationKey>();
    readonly current = this.selection.asReadonly();
    readonly t = (key: TranslationKey): string => translate(this.current(), key, undefined, missing => {
        if (isDevMode() && !this.reported.has(missing)) {
            this.reported.add(missing);
            console.warn(`[i18n] Missing reference translation: ${missing}`);
        }
    });

    constructor() {
        effect(() => {
            document.documentElement.lang = this.current();
            document.title = this.t('app.title');
        });
    }

    select(language: string): void {
        if (language !== 'es' && language !== 'en') return;
        this.selection.set(language);
        try {
            localStorage.setItem(STORAGE_KEY, language);
        } catch {
            // A blocked/full store must not prevent an immediate, session-local language change.
        }
    }
}