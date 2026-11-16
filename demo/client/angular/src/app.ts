import { Component, computed, inject, signal } from '@angular/core';
import { ThemeRegistry, ThemeService, ThemeShellOutlet } from '@alxarafe/ui-runtime';
import { RemoteDictionary } from './remote/dictionary';
import { LanguageService } from './i18n/language.service';
import type { TranslationKey } from './i18n/types';
import { CAPABILITIES, RUNTIMES, type RuntimeId } from './catalog';

@Component({
    selector: 'arp-demo',
    imports: [ThemeShellOutlet, RemoteDictionary],
    templateUrl: './app.html',
})
export class DemoApp {
    readonly i18n = inject(LanguageService);
    readonly t = this.i18n.t;
    readonly themes = inject(ThemeService);
    readonly registry = inject(ThemeRegistry);
    readonly runtimes = RUNTIMES;
    readonly capabilities = CAPABILITIES;
    readonly runtimeId = signal<RuntimeId>('dotnet');
    readonly runtime = computed(() => RUNTIMES.find(item => item.id === this.runtimeId())!);
    readonly capability = signal<typeof CAPABILITIES[number]>(CAPABILITIES[0]);
    readonly navigation = computed(() => CAPABILITIES.map(item => ({
        id: item.id, label: this.t(item.label), current: item.id === this.capability().id,
    })));
    readonly urls = signal<Record<RuntimeId, string>>({ dotnet: '', java: '', php: '' });
    readonly url = computed(() => this.urls()[this.runtimeId()]);
    readonly urlError = signal<TranslationKey | undefined>(undefined);
    readonly source = signal('');
    readonly content = signal('');
    readonly loading = signal(false);
    readonly error = signal<TranslationKey | undefined>(undefined);
    readonly revision = signal('');
    private loadSequence = 0;
    private readonly editedUrls = new Set<RuntimeId>();

    constructor() {
        void this.loadFile(CAPABILITIES[0].files[0]);
        void this.loadConfiguration();
    }

    private async loadConfiguration(): Promise<void> {
        try {
            const [configResponse, revisionResponse] = await Promise.all([
                fetch('instances.json'), fetch('revision.txt'),
            ]);
            if (!configResponse.ok || !revisionResponse.ok) throw new Error('configuration');
            const config: unknown = await configResponse.json();
            if (!config || typeof config !== 'object') throw new Error('configuration');
            const urls = { dotnet: '', java: '', php: '' };
            for (const runtime of RUNTIMES) {
                const value = (config as Record<string, unknown>)[runtime.id];
                if (typeof value !== 'string' || this.invalidUrl(value)) throw new Error('configuration');
                urls[runtime.id] = value;
            }
            // Do not overwrite an edit made while configuration was loading.
            this.urls.update(current => ({
                dotnet: this.editedUrls.has('dotnet') ? current.dotnet : urls.dotnet,
                java: this.editedUrls.has('java') ? current.java : urls.java,
                php: this.editedUrls.has('php') ? current.php : urls.php,
            }));
            this.revision.set(await revisionResponse.text());
        } catch {
            this.urlError.set('error.configuration');
        }
    }

    selectRuntime(event: Event): void {
        const id = (event.target as HTMLSelectElement).value;
        if (RUNTIMES.some(item => item.id === id)) this.runtimeId.set(id as RuntimeId);
        this.urlError.set(undefined);
    }

    private invalidUrl(value: string): boolean {
        if (!value) return false;
        try {
            const url = new URL(value);
            return !['http:', 'https:'].includes(url.protocol) || Boolean(url.username || url.password);
        } catch {
            return true;
        }
    }

    configureUrl(event: Event): void {
        const value = (event.target as HTMLInputElement).value.trim();
        this.editedUrls.add(this.runtimeId());
        if (this.invalidUrl(value)) {
            this.urlError.set('error.url');
            return;
        }
        this.urls.update(urls => ({ ...urls, [this.runtimeId()]: value }));
        this.urlError.set(undefined);
    }

    selectLanguage(event: Event): void {
        this.i18n.select((event.target as HTMLSelectElement).value);
    }

    selectTheme(event: Event): void {
        this.themes.activate((event.target as HTMLSelectElement).value);
    }

    selectCapability(id: string): void {
        const capability = CAPABILITIES.find(item => item.id === id);
        if (!capability) return;
        this.capability.set(capability);
        void this.loadFile(capability.files[0]);
    }

    selectFile(event: Event): void {
        void this.loadFile((event.target as HTMLSelectElement).value);
    }

    async loadFile(path: string): Promise<void> {
        if (!(this.capability().files as readonly string[]).includes(path)) return;
        const sequence = ++this.loadSequence;
        this.source.set(path);
        this.content.set('');
        this.error.set(undefined);
        this.loading.set(true);
        try {
            const response = await fetch(`contract/${path}`);
            if (!response.ok) throw new Error('asset');
            const text = await response.text();
            if (sequence === this.loadSequence) this.content.set(text);
        } catch {
            if (sequence === this.loadSequence) this.error.set('error.source');
        } finally {
            if (sequence === this.loadSequence) this.loading.set(false);
        }
    }
}