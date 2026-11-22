import { negotiate } from "./protocol";
import type { RuntimeId } from "../catalog";

export type Scalar = string | boolean | null;
export type Values = Record<string, Scalar>;
export const OPERATIONS = ["LIST", "GET", "CREATE", "UPDATE", "DELETE"] as const;
export type Operation = typeof OPERATIONS[number];
export interface Field {
    name: string;
    type: string;
    label: string;
    nullable: boolean;
    key: boolean;
    constraints: Record<string, unknown>;
}
export interface Metadata {
    demoProtocol: string;
    target: string;
    projection: string;
    fields: Field[];
    operations: Operation[];
    pagination: { defaultLimit: number; maxLimit: number; maxPage: number };
}
export interface RecordValue { key: object; values: Values; }
export interface Envelope {
    status: "success" | "conflict" | "rejected" | "failed";
    output?: Record<string, unknown>;
}

/** Exact numeric metadata stays distinguishable from portable scalar strings. */
export class ExactJsonNumber {
    constructor(readonly source: string) {}

    toJSON(): string {
        return this.source;
    }
}

/** Preserve scalar strings and exact numeric metadata, including fractions that round to integers. */
export function parseExact(text: string): unknown {
    return JSON.parse(text, (_key: string, value: unknown, context?: { source: string }) => {
        if (typeof value !== "number") return value;
        if (!context?.source) throw new Error("Exact JSON source support is required");
        return /^-?(0|[1-9][0-9]*)$/.test(context.source) && Number.isSafeInteger(value)
            ? value : new ExactJsonNumber(context.source);
    });
}

export function supportsCrud(runtime: RuntimeId, info: unknown): boolean {
    if (runtime !== "php" || !negotiate(runtime, info)) return false;
    const capabilities = (info as { capabilities: string[] }).capabilities;
    return ["crud.metadata", "crud.invoke"].every(item => capabilities.includes(item));
}

export function object(value: unknown): value is Record<string, unknown> {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

const TYPES = new Set(["STRING", "TEXT", "INTEGER", "DECIMAL", "BOOLEAN", "UUID", "DATE", "TIME",
    "DATETIME", "ENUM", "BINARY"]);

export function metadata(value: unknown): Metadata {
    if (!object(value) || value.demoProtocol !== "arp-demo-php-crud/1"
        || typeof value.target !== "string" || !value.target || typeof value.projection !== "string"
        || !Array.isArray(value.fields) || !value.fields.length || value.fields.length > 128
        || !Array.isArray(value.operations) || !value.operations.every(op => OPERATIONS.includes(op))
        || !object(value.pagination)) throw new Error("Invalid CRUD metadata");
    const fields = value.fields;
    for (const field of fields) {
        if (!object(field) || typeof field.name !== "string" || !field.name
            || typeof field.type !== "string" || !TYPES.has(field.type)
            || typeof field.label !== "string" || typeof field.nullable !== "boolean"
            || typeof field.key !== "boolean" || !object(field.constraints)) throw new Error("Invalid field");
    }
    if (new Set(fields.map(field => field.name)).size !== fields.length || !fields.some(field => field.key)) {
        throw new Error("Invalid fields");
    }
    const page = value.pagination;
    if (![page.defaultLimit, page.maxLimit, page.maxPage].every(n => Number.isSafeInteger(n))
        || (page.defaultLimit as number) < 1 || (page.maxLimit as number) < (page.defaultLimit as number)
        || (page.maxLimit as number) > 100 || (page.maxPage as number) < 1 || (page.maxPage as number) > 100) {
        throw new Error("Invalid pagination");
    }
    if (!object(value.update) || value.update.onConflict !== "reload"
        || !object(value.delete) || value.delete.privateEvidence !== false
        || value.delete.confirmation !== "complete displayed values") throw new Error("Unsupported preconditions");
    return value as unknown as Metadata;
}

export function record(value: unknown, fields: Field[]): RecordValue {
    if (!object(value) || !object(value.key) || !object(value.values)
        || Object.keys(value.values).length !== fields.length) throw new Error("Invalid record");
    const values = value.values;
    for (const field of fields) {
        const scalar = values[field.name];
        if (!(scalar === null && field.nullable)
            && typeof scalar !== (field.type === "BOOLEAN" ? "boolean" : "string")) {
            throw new Error("Invalid scalar kind");
        }
    }
    return value as unknown as RecordValue;
}

export function changes(fields: Field[], original: Values, draft: Values): Values {
    return Object.fromEntries(fields.filter(field => !field.key && draft[field.name] !== original[field.name])
        .map(field => [field.name, draft[field.name]]));
}
