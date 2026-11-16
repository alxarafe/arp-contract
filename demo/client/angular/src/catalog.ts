// Demo inventory, not runtime discovery or a normative capability protocol.
export const RUNTIMES = [
    { id: 'dotnet', label: '.NET', commit: 'd9a0acf', branch: 'main' },
    { id: 'java', label: 'Java', commit: '5888272', branch: 'main' },
    { id: 'php', label: 'PHP', commit: '6c4b781', branch: 'release/arp-dict-001-v0.1.0-rc1' },
] as const;
export type RuntimeId = typeof RUNTIMES[number]['id'];

export const CAPABILITIES = [
    {
        id: 'dictionary', label: 'Diccionario y validaciones', mark: '01',
        status: 'Biblioteca disponible · adaptador pendiente',
        detail: '17 tipos escalares en los tres runtimes. No hay un endpoint de validación en esta demo.',
        files: [
            'fixtures/dictionary/v1/catalog.json', 'fixtures/dictionary/v1/values.json',
            'fixtures/dictionary/v1/definitions.json', 'fixtures/dictionary/v1/catalogs.json',
        ],
    },
    {
        id: 'entities', label: 'Entidades y estructuras', mark: '02',
        status: 'Pendiente de implementación',
        detail: 'ARP-RES-001 es un borrador. Las estructuras compuestas no están implementadas.',
        files: ['docs/features/arp-res-001-borrador-especificacion.md', 'examples/demo/cds/logical.yaml'],
    },
    {
        id: 'projections', label: 'Proyecciones', mark: '03',
        status: 'Borrador con fixtures estáticos',
        detail: 'Las definiciones CDS no constituyen un motor de proyecciones ejecutable.',
        files: [
            'examples/demo/cds/public.yaml', 'examples/demo/cds/summary.yaml', 'fixtures/cds/v1/manifest.json',
        ],
    },
    {
        id: 'crud', label: 'CRUD', mark: '04', status: 'Pendiente de implementación',
        detail: 'Sin almacenamiento ni adaptador CRUD. Los escenarios describen expectativas contractuales.',
        files: ['fixtures/cds/v1/historical-updates.json', 'fixtures/services/v1/cases.json'],
    },
    {
        id: 'services', label: 'Servicios e invocaciones', mark: '05',
        status: 'Borrador con fixtures estáticos',
        detail: 'SERVICES-002 no es un dispatcher de runtime ni un protocolo de transporte publicado.',
        files: ['fixtures/services/v1/invocation-cases.json'],
    },
] as const;