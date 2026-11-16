import { Component, DestroyRef, effect, inject, input, signal } from '@angular/core';
import { LanguageService } from '../i18n/language.service';
import type { TranslationKey } from '../i18n/types';

interface ElementSummary { id: string; type: string; }
const TYPES = new Set([
    'BOOLEAN', 'STRING', 'TEXT', 'INT8', 'UINT8', 'INT16', 'UINT16', 'INT32', 'UINT32',
    'INT64', 'DECIMAL', 'UUID', 'DATE', 'TIME', 'DATETIME', 'ENUM', 'BINARY',
]);

/** Consumer of the documented .NET demo API only; not a generic ARP transport contract. */
@Component({
    selector: 'arp-dotnet-dictionary',
    templateUrl: './dictionary.html',
})
export class DotnetDictionary {
    readonly baseUrl = input.required<string>();
    readonly t = inject(LanguageService).t;
    readonly status = signal<TranslationKey>('remote.idle');
    readonly connected = signal(false);
    readonly busy = signal(false);
    readonly elements = signal<ElementSummary[]>([]);
    readonly selected = signal('');
    readonly descriptor = signal('');
    readonly result = signal('');
    readonly issue = signal<TranslationKey | undefined>(undefined);
    readonly codec = signal('string');
    readonly value = signal('');
    private controller = new AbortController();
    private sequence = 0;
    private target = '';

    constructor() {
        effect(() => { this.baseUrl(); this.disconnect(); });
        inject(DestroyRef).onDestroy(() => this.controller.abort());
    }

    private cancel(): number {
        this.controller.abort();
        this.controller = new AbortController();
        return ++this.sequence;
    }

    disconnect(): void {
        this.cancel();
        this.target = '';
        this.connected.set(false);
        this.busy.set(false);
        this.status.set('remote.idle');
        this.elements.set([]);
        this.selected.set('');
        this.descriptor.set('');
        this.result.set('');
        this.issue.set(undefined);
    }

    private async request(path: string, body?: string): Promise<Response> {
        const response = await fetch(`${this.target}${path}`, {
            method: body === undefined ? 'GET' : 'POST',
            headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
            body, credentials: 'omit', redirect: 'error',
            signal: AbortSignal.any([this.controller.signal, AbortSignal.timeout(8000)]),
        });
        return response;
    }

    private failed(sequence: number, key: TranslationKey = 'remote.failed'): void {
        if (sequence !== this.sequence) return;
        this.connected.set(false);
        this.status.set('remote.failed');
        this.issue.set(key);
    }

    async connect(): Promise<void> {
        this.disconnect();
        if (!this.baseUrl()) return;
        this.target = this.baseUrl().replace(/\/$/, '');
        const sequence = this.sequence;
        this.status.set('remote.connecting');
        this.busy.set(true);
        try {
            const infoResponse = await this.request('/demo/info');
            if (!infoResponse.ok) throw new Error('HTTP');
            const info = await infoResponse.json(); // This envelope contains strings only, no numeric descriptors.
            if (info.demoProtocol !== 'arp-demo-dotnet/1' || info.runtime !== 'dotnet'
                || !Array.isArray(info.capabilities)
                || !['dictionary.list', 'dictionary.describe', 'dictionary.validate']
                    .every(capability => info.capabilities.includes(capability))) {
                this.failed(sequence, 'remote.incompatible');
                return;
            }
            const response = await this.request('/demo/dictionary/elements');
            if (!response.ok) throw new Error('HTTP');
            const listing = await response.json(); // IDs and scalar type names only.
            if (!Array.isArray(listing.elements) || listing.elements.length === 0
                || !listing.elements.every((item: ElementSummary) => item && typeof item.id === 'string'
                    && typeof item.type === 'string' && TYPES.has(item.type))
                || new Set(listing.elements.map((item: ElementSummary) => item.id)).size !== listing.elements.length) {
                throw new Error('Invalid listing');
            }
            if (sequence !== this.sequence) return;
            this.elements.set(listing.elements);
            this.connected.set(true);
            this.status.set('remote.connected');
        } catch {
            this.failed(sequence);
        } finally {
            if (sequence === this.sequence) this.busy.set(false);
        }
    }

    async selectElement(event: Event): Promise<void> {
        const id = (event.target as HTMLSelectElement).value;
        const item = this.elements().find(element => element.id === id);
        const sequence = this.cancel();
        this.selected.set(item?.id ?? '');
        this.descriptor.set('');
        this.result.set('');
        this.issue.set(undefined);
        if (!item || !this.connected()) return;
        this.codec.set(item.type === 'BOOLEAN' ? 'boolean' : 'string');
        this.value.set(item.type === 'BOOLEAN' ? 'true' : '');
        this.busy.set(true);
        try {
            const response = await this.request(`/demo/dictionary/elements/${encodeURIComponent(id)}`);
            if (!response.ok) throw new Error('HTTP');
            const text = await response.text(); // Do not parse numeric metadata into JavaScript Number.
            if (sequence === this.sequence) this.descriptor.set(text);
        } catch {
            this.failed(sequence);
        } finally {
            if (sequence === this.sequence) this.busy.set(false);
        }
    }

    setValue(event: Event): void {
        this.value.set((event.target as HTMLInputElement).value);
        this.result.set('');
    }
    setCodec(event: Event): void {
        this.codec.set((event.target as HTMLSelectElement).value);
        this.value.set(this.codec() === 'boolean' ? 'true' : '');
        this.result.set('');
    }

    async validate(): Promise<void> {
        if (!this.connected() || !this.selected() || this.busy()) return;
        const sequence = this.cancel();
        this.busy.set(true);
        this.result.set('');
        this.issue.set(undefined);
        const value = this.codec() === 'null' ? null : this.codec() === 'boolean'
            ? this.value() === 'true' : this.value();
        try {
            const response = await this.request(
                `/demo/dictionary/elements/${encodeURIComponent(this.selected())}/validate`, JSON.stringify({ value }));
            const text = await response.text(); // Preserve the original result, including normalized exact strings.
            if (sequence !== this.sequence) return;
            this.result.set(text);
            if (!response.ok) this.failed(sequence, 'remote.httpError');
        } catch {
            this.failed(sequence);
        } finally {
            if (sequence === this.sequence) this.busy.set(false);
        }
    }
}