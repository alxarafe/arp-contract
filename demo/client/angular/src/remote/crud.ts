import { Component, DestroyRef, effect, inject, input, signal } from "@angular/core";
import { LanguageService } from "../i18n/language.service";
import type { TranslationKey } from "../i18n/types";
import type { RuntimeId } from "../catalog";
import { changes, metadata, object, parseExact, record, supportsCrud } from "./crud-protocol";
import type { Envelope, Field, Metadata, Operation, RecordValue, Scalar, Values } from "./crud-protocol";

@Component({ selector: "arp-remote-crud", templateUrl: "./crud.html" })
export class RemoteCrud {
    readonly baseUrl = input.required<string>();
    readonly runtimeId = input.required<RuntimeId>();
    readonly t = inject(LanguageService).t;
    readonly token = signal("");
    readonly meta = signal<Metadata | undefined>(undefined);
    readonly rows = signal<RecordValue[]>([]);
    readonly selected = signal<RecordValue | undefined>(undefined);
    readonly mode = signal<"create" | "view" | "edit" | "delete" | undefined>(undefined);
    readonly draft = signal<Values>({});
    readonly page = signal(1);
    readonly limit = signal(10);
    readonly next = signal<number | null>(null);
    readonly busy = signal(false);
    readonly blocked = signal(false);
    readonly consent = signal(false);
    readonly status = signal<TranslationKey>("remote.idle");
    readonly issue = signal<TranslationKey | undefined>(undefined);
    readonly result = signal("");
    private controller = new AbortController();
    private sequence = 0;
    private target = "";
    private credential = "";

    constructor() {
        effect(() => { this.baseUrl(); this.runtimeId(); this.disconnect(); });
        inject(DestroyRef).onDestroy(() => this.disconnect());
    }

    disconnect(): void {
        this.controller.abort();
        this.controller = new AbortController();
        ++this.sequence;
        this.target = "";
        this.credential = "";
        this.token.set("");
        this.meta.set(undefined);
        this.rows.set([]);
        this.close();
        this.page.set(1);
        this.next.set(null);
        this.busy.set(false);
        this.issue.set(undefined);
        this.result.set("");
        this.status.set("remote.idle");
    }

    can(operation: Operation): boolean {
        return this.meta()?.operations.includes(operation) ?? false;
    }

    private async request(path: string, inputs?: object): Promise<{ response: Response; text: string; data: unknown }> {
        const response = await fetch(`${this.target}${path}`, {
            method: inputs === undefined ? "GET" : "POST",
            headers: { Authorization: `Bearer ${this.credential}`, ...(inputs === undefined ? {}
                : { "Content-Type": "application/json" }) },
            body: inputs === undefined ? undefined : JSON.stringify(inputs),
            credentials: "omit", redirect: "error", cache: "no-store",
            signal: AbortSignal.any([this.controller.signal, AbortSignal.timeout(10000)]),
        });
        const text = await response.text();
        return { response, text, data: parseExact(text) };
    }

    private async task(action: (sequence: number) => Promise<void>): Promise<void> {
        if (this.busy()) return;
        const sequence = this.sequence;
        this.busy.set(true);
        this.issue.set(undefined);
        try {
            await action(sequence);
        } catch {
            if (sequence === this.sequence) this.issue.set("crud.failed");
        } finally {
            if (sequence === this.sequence) this.busy.set(false);
        }
    }

    async connect(): Promise<void> {
        if (this.busy() || !this.baseUrl() || !this.token()) return;
        const credential = this.token();
        this.disconnect();
        this.credential = credential;
        this.target = this.baseUrl().replace(/\/$/, "");
        this.status.set("remote.connecting");
        const session = this.sequence;
        await this.task(async sequence => {
            // Never send the credential to discovery; only the recognized PHP adapter receives it.
            const response = await fetch(`${this.target}/demo/info`, {
                credentials: "omit", redirect: "error", cache: "no-store",
                signal: AbortSignal.any([this.controller.signal, AbortSignal.timeout(10000)]),
            });
            const info = parseExact(await response.text());
            if (sequence !== this.sequence) return;
            if (!response.ok || !supportsCrud(this.runtimeId(), info)) {
                this.issue.set("crud.unsupported");
                this.status.set("remote.failed");
                this.credential = "";
                return;
            }
            const reply = await this.request("/demo/crud/metadata");
            if (sequence !== this.sequence) return;
            if (!reply.response.ok) {
                this.result.set(reply.text);
                this.issue.set(reply.response.status === 403 ? "crud.unauthorized" : "remote.httpError");
                this.status.set("remote.failed");
                this.credential = "";
                return;
            }
            const meta = metadata(reply.data);
            this.meta.set(meta);
            this.limit.set(meta.pagination.defaultLimit);
            this.status.set("remote.connected");
            if (this.can("LIST")) await this.list(1, sequence);
        });
        if (session === this.sequence && !this.meta()) {
            this.credential = "";
            this.status.set("remote.failed");
        }
    }

    private async invoke(operation: Operation, inputs: object, sequence: number): Promise<Envelope | undefined> {
        const meta = this.meta();
        if (!meta || !this.can(operation)) throw new Error("Unavailable");
        const reply = await this.request("/demo/crud/invoke", { target: meta.target, operation, inputs });
        if (sequence !== this.sequence) return undefined;
        if (reply.response.status === 403) {
            this.result.set(reply.text);
            this.credential = "";
            this.meta.set(undefined);
            this.rows.set([]);
            this.close();
            this.status.set("remote.failed");
            this.issue.set("crud.unauthorized");
            return undefined;
        }
        if (!object(reply.data) || !["success", "conflict", "rejected", "failed"].includes(String(reply.data.status))) {
            this.result.set(reply.text);
            throw new Error("Invalid response");
        }
        const envelope = reply.data as unknown as Envelope;
        if (!reply.response.ok || envelope.status !== "success") {
            this.result.set(reply.text);
            this.issue.set(reply.response.status === 403 ? "crud.unauthorized"
                : envelope.status === "conflict" ? "crud.conflict" : "remote.httpError");
            if (envelope.status === "conflict" || reply.response.status >= 500) this.blocked.set(true);
            return undefined;
        }
        if (operation !== "LIST" && operation !== "GET") this.result.set(reply.text);
        return envelope;
    }

    private async list(page: number, sequence: number): Promise<void> {
        const meta = this.meta()!;
        const reply = await this.invoke("LIST", { page, limit: this.limit() }, sequence);
        if (!reply) return;
        const output = reply.output;
        if (!output || !Array.isArray(output.records) || !object(output.page)
            || !(output.page.next === null || Number.isSafeInteger(output.page.next))) throw new Error("Invalid page");
        this.rows.set(output.records.map(row => record(row, meta.fields)));
        this.page.set(page);
        const next = output.page.next as number | null;
        this.next.set(next !== null && next <= meta.pagination.maxPage ? next : null);
    }

    async loadPage(page: number): Promise<void> {
        if (!this.can("LIST") || page < 1 || page > this.meta()!.pagination.maxPage) return;
        await this.task(sequence => this.list(page, sequence));
    }

    async open(row: RecordValue, mode: "view" | "delete" = "view"): Promise<void> {
        if (!this.can("GET")) return;
        await this.task(async sequence => {
            const reply = await this.invoke("GET", { key: row.key }, sequence);
            if (!reply) return;
            if (reply.output?.found !== true) {
                this.close();
                this.issue.set("crud.missing");
                return;
            }
            const current = record(reply.output.record, this.meta()!.fields);
            this.selected.set(current);
            this.draft.set({ ...current.values });
            this.mode.set(mode);
            this.blocked.set(false);
            this.consent.set(false);
        });
    }

    create(): void {
        if (!this.can("CREATE") || this.busy()) return;
        this.close();
        this.draft.set(Object.fromEntries(this.meta()!.fields.map(field =>
            [field.name, field.nullable ? null : field.type === "BOOLEAN" ? false : ""])));
        this.mode.set("create");
        this.result.set("");
    }

    edit(): void {
        if (this.can("UPDATE") && this.selected() && !this.blocked() && !this.busy()) this.mode.set("edit");
    }

    close(): void {
        this.selected.set(undefined);
        this.mode.set(undefined);
        this.draft.set({});
        this.blocked.set(false);
        this.consent.set(false);
    }

    value(field: Field, event: Event): void {
        const value = field.type === "BOOLEAN" ? (event.target as HTMLInputElement).checked
            : (event.target as HTMLInputElement).value;
        this.draft.update(draft => ({ ...draft, [field.name]: value }));
    }

    nullable(field: Field, event: Event): void {
        const value = (event.target as HTMLInputElement).checked ? null : field.type === "BOOLEAN" ? false : "";
        this.draft.update(draft => ({ ...draft, [field.name]: value }));
    }

    display(value: Scalar | undefined): string {
        return value === null ? "null" : value === undefined ? "" : String(value);
    }

    constraints(field: Field): string {
        return JSON.stringify(field.constraints);
    }

    async save(event: Event): Promise<void> {
        event.preventDefault();
        if (this.blocked() || !["create", "edit"].includes(this.mode() ?? "")) return;
        await this.task(async sequence => {
            const creating = this.mode() === "create";
            const current = this.selected();
            const changed = creating ? this.draft() : changes(this.meta()!.fields, current!.values, this.draft());
            let reply: Envelope | undefined;
            try {
                reply = await this.invoke(creating ? "CREATE" : "UPDATE", creating ? { values: changed }
                    : { key: current!.key, changes: changed, baseline: current!.values }, sequence);
            } catch (error) {
                if (sequence === this.sequence) this.blocked.set(true);
                throw error;
            }
            if (!reply) return;
            this.close();
            if (this.can("LIST")) await this.list(this.page(), sequence);
        });
    }

    async remove(): Promise<void> {
        if (this.mode() !== "delete" || !this.consent() || this.blocked() || !this.selected()) return;
        await this.task(async sequence => {
            const shown = this.selected()!;
            let reply: Envelope | undefined;
            try {
                reply = await this.invoke("DELETE", { key: shown.key, confirmedValues: shown.values }, sequence);
            } catch (error) {
                if (sequence === this.sequence) this.blocked.set(true);
                throw error;
            }
            if (!reply) return;
            this.close();
            if (this.can("LIST")) await this.list(1, sequence);
        });
    }
}
