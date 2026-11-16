import type { TranslationKey } from './i18n/types';

// Demo inventory, not runtime discovery or a normative capability protocol.
export const RUNTIMES = [
    { id: 'dotnet', label: '.NET', commit: 'd9a0acf', branch: 'main' },
    { id: 'java', label: 'Java', commit: '5888272', branch: 'main' },
    { id: 'php', label: 'PHP', commit: '6c4b781', branch: 'release/arp-dict-001-v0.1.0-rc1' },
] as const;
export type RuntimeId = typeof RUNTIMES[number]['id'];

export const CAPABILITIES = [
    {
        id: 'dictionary', label: 'dictionary.label', mark: '01',
        status: 'dictionary.status',
        detail: 'dictionary.detail',
        files: [
            'fixtures/dictionary/v1/catalog.json', 'fixtures/dictionary/v1/values.json',
            'fixtures/dictionary/v1/definitions.json', 'fixtures/dictionary/v1/catalogs.json',
        ],
    },
    {
        id: 'entities', label: 'entities.label', mark: '02',
        status: 'entities.status',
        detail: 'entities.detail',
        files: ['docs/features/arp-res-001-borrador-especificacion.md', 'examples/demo/cds/logical.yaml'],
    },
    {
        id: 'projections', label: 'projections.label', mark: '03',
        status: 'projections.status',
        detail: 'projections.detail',
        files: [
            'examples/demo/cds/public.yaml', 'examples/demo/cds/summary.yaml', 'fixtures/cds/v1/manifest.json',
        ],
    },
    {
        id: 'crud', label: 'crud.label', mark: '04', status: 'crud.status',
        detail: 'crud.detail',
        files: ['fixtures/cds/v1/historical-updates.json', 'fixtures/services/v1/cases.json'],
    },
    {
        id: 'services', label: 'services.label', mark: '05',
        status: 'services.status',
        detail: 'services.detail',
        files: ['fixtures/services/v1/invocation-cases.json'],
    },
] as const satisfies readonly {
    id: string;
    label: TranslationKey;
    mark: string;
    status: TranslationKey;
    detail: TranslationKey;
    files: readonly string[];
}[];