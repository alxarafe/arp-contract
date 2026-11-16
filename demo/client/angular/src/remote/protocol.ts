import type { RuntimeId } from '../catalog';

// Recognized demo adapters only. These pairs do not publish a normative ARP transport.
const PROTOCOLS: Readonly<Record<RuntimeId, string>> = {
    dotnet: 'arp-demo-dotnet/1', java: 'arp-demo-java/1', php: 'arp-demo-php/1',
};
export const DICTIONARY_CAPABILITIES = ['dictionary.list', 'dictionary.describe', 'dictionary.validate'] as const;
export type DictionaryCapability = typeof DICTIONARY_CAPABILITIES[number];

export function negotiate(runtime: RuntimeId, info: unknown): readonly DictionaryCapability[] | undefined {
    if (!info || typeof info !== 'object') return undefined;
    const envelope = info as Record<string, unknown>;
    const capabilities = envelope.capabilities;
    if (envelope.runtime !== runtime || envelope.demoProtocol !== PROTOCOLS[runtime]
        || !Array.isArray(capabilities)
        || !capabilities.every((item: unknown) => typeof item === 'string')) return undefined;
    return DICTIONARY_CAPABILITIES.filter(capability => capabilities.includes(capability));
}