"""Pure candidate fixture profile. No package discovery, cache backend, renderer or authorization engine."""
from copy import deepcopy
import hashlib
from pathlib import Path

import check_cds_read_draft as cds
from check_contract import contract_validator, descriptor_projection, load

ROOT = Path(__file__).resolve().parents[1]
MODULE_SCHEMA = load(ROOT / 'schemas/modules/v1/module.schema.json')
MENU_SCHEMA = load(ROOT / 'schemas/menus/v1/menu-source.schema.json')
COMPOSITION_SCHEMA = load(ROOT / 'schemas/menus/v1/composition.schema.json')
MODULE_VALIDATOR = contract_validator(MODULE_SCHEMA)
SOURCE_VALIDATOR = contract_validator(MODULE_SCHEMA['properties']['sources']['items'])
MENU_VALIDATOR = contract_validator(MENU_SCHEMA)
COMPOSITION_VALIDATOR = contract_validator(COMPOSITION_SCHEMA)
DICT_VALIDATOR = contract_validator(load(ROOT / 'schemas/dictionary/v1/dictionary.schema.json'))


class Rejected(ValueError):
    def __init__(self, code, at, family='definition-invalid'):
        self.issue = {'family': family, 'code': code, 'at': at}


def require(ok, code, at):
    if not ok:
        raise Rejected(code, at)


def failure(error):
    return {'valid': False, 'issues': [error.issue]}


def stamp(value):
    return hashlib.sha256(repr(cds.canonical(value)).encode('utf-8')).hexdigest()


def source_key(source):
    return ('source', source['providerId'], source['sourceId'])


def required_dependency(owner, target_owner, dependencies):
    if owner[0] == target_owner[0] == 'module' and owner != target_owner:
        require(target_owner[1] in dependencies[owner[1]],
                'MODULES_DEPENDENCY_UNDECLARED', '/dependencies')


def definition_references(definitions, owners, dependencies, sources, evidence):
    """Known consumers report typed mandatory references, never guesses from strings or paths."""
    for kind in ('logical', 'projection'):
        for identity, document in sorted(definitions.get(kind, {}).items()):
            if kind == 'logical':
                targets = [('physical', document['physical'])]
                targets += [('dictionary', field['dictionary']) for field in document['fields'].values()
                            if 'dictionary' in field]
            else:
                source = document['source']
                targets = [('logical', source['entity'])] if 'entity' in source else [
                    ('projection', source['projection'])]
            for target in targets:
                required_dependency(owners[(kind, identity)], owners[target], dependencies)
    # Private fixture evidence stands for the mandatory-reference result of registered extension processors.
    source_owners = {source_key(source): tuple(source['owner']) for source in sources}
    for item in evidence:
        origin = ('source', item['source']['providerId'], item['source']['sourceId'])
        target = (item['target']['kind'], item['target']['id'])
        require(origin in source_owners and target in owners, 'MODULES_REFERENCE_MISSING', '/definitions')
        required_dependency(source_owners[origin], owners[target], dependencies)


def activate(assets, host):
    """Stage immutable active sources and existing CDS definitions, never publish or delete anything."""
    try:
        modules = host.get('modules', assets['modules'])
        requested = host['active']
        require(isinstance(modules, list) and isinstance(requested, list)
                and all(isinstance(identity, str) for identity in requested), 'MODULES_ACTIVE_INVALID', '/active')
        require(len(modules) <= 256 and len(requested) <= 256, 'MODULES_LIMIT', '/modules')
        require(len(set(requested)) == len(requested), 'MODULES_ACTIVE_INVALID', '/active')
        index = {}
        for module in modules:
            require(MODULE_VALIDATOR.is_valid(module), 'MODULES_SCHEMA_INVALID', '/modules')
            require(module['id'] not in index, 'MODULES_DUPLICATE_ID', '/modules')
            index[module['id']] = module
        require(set(requested) <= set(index), 'MODULES_NOT_FOUND', '/active')
        order, visited = [], set()

        def visit(identity, stack):
            require(identity not in stack, 'MODULES_DEPENDENCY_CYCLE', '/dependencies')
            if identity in visited:
                return
            for dependency in sorted(index[identity]['dependencies']):
                require(dependency in index, 'MODULES_DEPENDENCY_MISSING', '/dependencies')
                require(dependency in requested, 'MODULES_DEPENDENCY_INACTIVE', '/dependencies')
                visit(dependency, stack + [identity])
            visited.add(identity)
            order.append(identity)

        for identity in sorted(requested):
            visit(identity, [])
        registrations = [(('application', host['applicationId']), source)
                         for source in host.get('applicationSources', assets['applicationSources'])]
        registrations += [(('module', identity), source) for identity in order for source in index[identity]['sources']]
        require(len(registrations) <= 1024, 'MODULES_LIMIT', '/sources')
        require(all(SOURCE_VALIDATOR.is_valid(source) for _, source in registrations),
                'MODULES_SCHEMA_INVALID', '/sources')
        definitions, owners, menus, inputs, selections, sources = {}, {}, [], {}, {}, []
        payloads = host.get('payloads', assets['payloads'])
        for owner, source in sorted(registrations, key=lambda pair: source_key(pair[1])):
            require(SOURCE_VALIDATOR.is_valid(source), 'MODULES_SCHEMA_INVALID', '/sources')
            key = source_key(source)
            require(key not in inputs, 'MODULES_SOURCE_CONFLICT', '/sources')
            kind = source['kind']
            require(kind in host['registeredKinds'], 'MODULES_KIND_UNSUPPORTED', '/sources')
            if source['handle'] not in payloads:
                raise Rejected('MODULES_SOURCE_UNAVAILABLE', '/sources', 'execution-failure')
            payload = deepcopy(payloads[source['handle']])
            inputs[key] = stamp({'revision': source['revision'], 'payload': payload, 'owner': list(owner)})
            sources.append({'owner': list(owner), **deepcopy(source)})
            if kind == 'menu':
                require(MENU_VALIDATOR.is_valid(payload), 'MODULES_SOURCE_INVALID', '/sources')
                menus.append((key, payload))
                targets = [menu['id'] for menu in payload.get('menus', [])]
                targets += [part['menu'] for part in payload.get('contributions', [])]
                for target in targets:
                    selections.setdefault(('selection', 'menu', target), set()).add(key)
                continue
            if kind == 'dictionary':
                require(DICT_VALIDATOR.is_valid(payload), 'MODULES_SOURCE_INVALID', '/sources')
                documents = payload['elements']
            elif kind in {'physical', 'logical', 'projection'}:
                documents = [payload]
            else:
                # Registered fixture handler only: no translation/future-type grammar is standardized here.
                require(isinstance(payload, list) and all(isinstance(doc, dict) and 'id' in doc for doc in payload),
                        'MODULES_SOURCE_INVALID', '/sources')
                documents = payload
            for document in documents:
                identity = document.get('id')
                require(isinstance(identity, str), 'MODULES_SOURCE_INVALID', '/sources')
                require(identity not in definitions.setdefault(kind, {}), 'MODULES_DEFINITION_CONFLICT', '/sources')
                definitions[kind][identity] = deepcopy(document)
                owners[(kind, identity)] = owner
                selections.setdefault(('selection', kind, identity), set()).add(key)
        dictionary = {key: descriptor_projection(value) for key, value in definitions.get('dictionary', {}).items()}
        bundle = {plural: definitions.get(singular, {}) for plural, singular in
                  [('physical', 'physical'), ('logical', 'logical'), ('projections', 'projection')]}
        resolved = cds.resolve(bundle, dictionary)
        if not resolved['valid']:
            raise Rejected('MODULES_CDS_INVALID', '/definitions', resolved['issues'][0]['family'])
        dependencies = {identity: set(index[identity]['dependencies']) for identity in order}
        definition_references(definitions, owners, dependencies, sources, host.get('processorReferences', []))
        for selector, keys in selections.items():
            inputs[selector] = stamp([[list(key), inputs[key]] for key in sorted(keys)])
        result = {'valid': True, 'issues': [], 'activeModules': order, 'sources': sources,
                  'definitions': definitions, 'owners': owners, 'menuSources': menus, 'cds': resolved,
                  'inputs': inputs, 'applicationId': host['applicationId'], 'dependencies': dependencies}
        return result
    except Rejected as error:
        return failure(error)


def module_summary(snapshot):
    if not snapshot['valid']:
        return snapshot
    return {'valid': True, 'issues': [], 'activeModules': snapshot['activeModules'],
            'sources': sorted(source['providerId'] + ':' + source['sourceId'] for source in snapshot['sources']),
            'definitions': {kind: sorted(docs) for kind, docs in sorted(snapshot['definitions'].items())}}


def compose(snapshot, composition, host):
    """Merge candidate menu contributions, explicit application edits, then trusted host visibility."""
    if not snapshot['valid']:
        return snapshot
    try:
        require(COMPOSITION_VALIDATOR.is_valid(composition), 'MENUS_COMPOSITION_INVALID', '/composition')
        menus, entries, menu_owners = {}, {}, {}
        source_owners = {source_key(source): tuple(source['owner']) for source in snapshot['sources']}
        for source_id, source in snapshot['menuSources']:
            for menu in source.get('menus', []):
                require(menu['id'] not in menus, 'MENUS_MENU_CONFLICT', '/menus')
                menus[menu['id']] = {'id': menu['id'], 'scope': menu['scope']}
                entries[menu['id']] = []
                menu_owners[menu['id']] = source_owners[source_id]
        contribution_owners = []
        for source_id, source in snapshot['menuSources']:
            owner = source_owners[source_id]
            for menu in source.get('menus', []):
                entries[menu['id']] += [(deepcopy(entry), owner) for entry in menu['entries']]
            for part in source.get('contributions', []):
                require(part['menu'] in menus, 'MENUS_MENU_MISSING', '/contributions')
                entries[part['menu']] += [(deepcopy(entry), owner) for entry in part['entries']]
                contribution_owners.append((owner, menu_owners[part['menu']]))
        require(sum(map(len, entries.values())) <= 4096, 'MENUS_LIMIT', '/entries')
        indexes, entry_owners = {}, {}
        for identity in sorted(menus):
            index = {}
            for entry, owner in entries[identity]:
                require(entry['id'] not in index, 'MENUS_ENTRY_CONFLICT', '/entries')
                index[entry['id']] = {'parent': None, 'order': 0, **entry}
                entry_owners[(identity, entry['id'])] = owner
            indexes[identity] = index
        # Application edits do not repair an undeclared dependency of an authored module contribution.
        for owner, target_owner in contribution_owners:
            required_dependency(owner, target_owner, snapshot['dependencies'])
        # Fixture translation processor reports owners of known keys, without inferring ID namespaces.
        label_owners = {}
        for identity, document in snapshot['definitions'].get('translations', {}).items():
            for key in document.get('fixtureLabels', {}):
                label_owners.setdefault(key, set()).add(snapshot['owners'][('translations', identity)])
        for menu_id, index in sorted(indexes.items()):
            for identity, entry in sorted(index.items()):
                owner = entry_owners[(menu_id, identity)]
                for target_owner in label_owners.get(entry.get('labelKey'), set()):
                    required_dependency(owner, target_owner, snapshot['dependencies'])
                parent = entry['parent']
                if parent in index:
                    required_dependency(owner, entry_owners[(menu_id, parent)], snapshot['dependencies'])
                destination = entry.get('destination', {})
                target = ('projection', destination.get('target'))
                if destination.get('kind') == 'projection' and target in snapshot['owners']:
                    required_dependency(owner, snapshot['owners'][target], snapshot['dependencies'])
        edits, excluded = set(), set()
        for edit in sorted(composition['edits'], key=lambda item: (item['menu'], item['entry'])):
            key = (edit['menu'], edit['entry'])
            require(key not in edits, 'MENUS_EDIT_CONFLICT', '/composition')
            edits.add(key)
            if edit['menu'] not in indexes or edit['entry'] not in indexes[edit['menu']]:
                require(edit.get('whenMissing', 'error') == 'ignore', 'MENUS_EDIT_MISSING', '/composition')
                continue
            entry = indexes[edit['menu']][edit['entry']]
            changes = deepcopy(edit.get('changes', {}))
            if 'label' in changes:
                entry.pop('labelKey', None)
            if 'labelKey' in changes:
                entry.pop('label', None)
            if changes.get('destination', False) is None:
                changes.pop('destination')
                entry.pop('destination', None)
            entry.update(changes)
            if edit.get('exclude', False):
                excluded.add(key)
        projections = {p['id']: p for p in snapshot['cds']['projections']}
        output = []
        for identity, menu in sorted(menus.items()):
            index = indexes[identity]

            def ancestors(name, stack):
                require(name not in stack, 'MENUS_CYCLE', '/entries')
                require(len(stack) < 64, 'MENUS_LIMIT', '/entries')
                parent = index[name]['parent']
                if parent is not None:
                    require(parent in index, 'MENUS_PARENT_MISSING', '/entries')
                    ancestors(parent, stack + [name])

            hidden = {name for mid, name in excluded if mid == identity}
            for name, entry in sorted(index.items()):
                ancestors(name, [])
                destination = entry.get('destination')
                if destination is None:
                    continue
                kind, target = destination['kind'], destination['target']
                if kind == 'projection':
                    require(target in projections, 'MENUS_TARGET_MISSING', '/entries')
                    operation = destination.get('operation')
                    require(operation in projections[target]['operations'], 'MENUS_OPERATION_UNAVAILABLE', '/entries')
                    access = host['projectionAccess'].get(target, {})
                    if operation not in access.get('available', []) or operation not in access.get('authorized', []):
                        hidden.add(name)
                else:
                    require(kind in host['destinationKinds'], 'MENUS_DESTINATION_UNSUPPORTED', '/entries')
                    require(target in host['registeredDestinations'].get(kind, []),
                            'MENUS_TARGET_MISSING', '/entries')
                if kind != 'projection' and (kind + ':' + target) not in host['allowedDestinations']:
                    hidden.add(name)
            while True:
                expanded = hidden | {name for name, entry in index.items() if entry['parent'] in hidden}
                if expanded == hidden:
                    break
                hidden = expanded

            def children(parent):
                result = []
                selected = [entry for entry in index.values() if entry['parent'] == parent]
                for entry in sorted(selected, key=lambda item: (item['order'], item['id'])):
                    if entry['id'] in hidden:
                        continue
                    descendants = children(entry['id'])
                    if 'destination' not in entry and not descendants:
                        continue
                    node = {key: deepcopy(value) for key, value in entry.items() if key != 'parent'}
                    node['order'] = int(node['order'])
                    node['children'] = descendants
                    result.append(node)
                return result

            output.append({**menu, 'entries': children(None)})
        return {'valid': True, 'issues': [], 'menus': output}
    except Rejected as error:
        return failure(error)


def staged(assets, host):
    snapshot = activate(assets, host)
    composition = host.get('composition', assets['composition'])
    menus = compose(snapshot, composition, host)
    if snapshot['valid'] and menus['valid']:
        for menu in menus['menus']:
            edits = [edit for edit in composition['edits'] if edit['menu'] == menu['id']]
            snapshot['inputs'][('configuration', 'composition:' + menu['id'])] = stamp(
                sorted(edits, key=lambda edit: edit['entry']))
        snapshot['inputs'][('context', host['contextKey'])] = stamp({key: host[key] for key in
            ('contextRevision', 'allowedDestinations', 'registeredDestinations',
             'destinationKinds', 'projectionAccess')})
    return snapshot, menus


def dependency_key(item):
    kind = item['kind']
    if kind == 'source':
        return (kind, item['providerId'], item['sourceId'])
    if kind == 'selection':
        return (kind, item['type'], item['id'])
    return (kind, item['id'])


def cache_plan(before, after, cache):
    """Only invalidation planning in one logical application cache, not an implementation of ARP-CACHE."""
    try:
        require(before['valid'] and after['valid'], 'MODULES_STAGE_INVALID', '/cache')
        require(before['applicationId'] == after['applicationId'] == cache['applicationId'],
                'MODULES_CACHE_SCOPE', '/cache')
        entries = cache['entries']
        require(len(entries) <= 4096, 'MODULES_LIMIT', '/cache')
        index = {entry['id']: entry for entry in entries}
        require(len(index) == len(entries), 'MODULES_CACHE_GRAPH', '/cache')
        heights = {}

        def visit(identity, stack):
            require(identity not in stack, 'MODULES_CACHE_GRAPH', '/cache')
            require(len(stack) < 64, 'MODULES_LIMIT', '/cache')
            if identity in heights:
                require(len(stack) + heights[identity] <= 64, 'MODULES_LIMIT', '/cache')
                return heights[identity]
            height = 1
            for dependency in index[identity]['dependsOn']:
                require(dependency['kind'] in {'artifact', 'source', 'selection', 'configuration', 'context'},
                        'MODULES_CACHE_GRAPH', '/cache')
                key = dependency_key(dependency)
                if key[0] == 'artifact':
                    require(key[1] in index, 'MODULES_CACHE_GRAPH', '/cache')
                    height = max(height, 1 + visit(key[1], stack + [identity]))
                elif key[0] != 'selection':
                    require(key in before['inputs'], 'MODULES_CACHE_GRAPH', '/cache')
            heights[identity] = height
            return height

        for identity in sorted(index):
            visit(identity, [])
        old, new = before['inputs'], after['inputs']
        changed = {key for key in old.keys() | new.keys() if old.get(key) != new.get(key)}
        invalidated = set()
        while True:
            affected = {identity for identity, entry in index.items()
                        if any(dependency_key(dep) in changed for dep in entry['dependsOn'])
                        or (changed and entry.get('complete') is not True)}
            if affected <= invalidated:
                break
            invalidated |= affected
            changed |= {('artifact', identity) for identity in affected}
        return {'valid': True, 'issues': [], 'invalidated': sorted(invalidated),
                'retained': sorted(index.keys() - invalidated)}
    except Rejected as error:
        return failure(error)


def case_host(assets, patch):
    return {**deepcopy(assets['defaults']), **deepcopy(patch)}


def transition(assets, case):
    """A rejected candidate leaves the old, explicitly identified publication and cache unchanged."""
    original = deepcopy((assets, case))
    before, old_menus = staged(assets, case_host(assets, case['before']))
    assert before['valid'] and old_menus['valid'], 'Lifecycle vector must start with a valid publication'
    after, new_menus = staged(assets, case_host(assets, case['after']))
    decision = new_menus if not new_menus['valid'] else cache_plan(before, after, case['cache'])
    accepted = decision['valid']
    return {'valid': accepted, 'issues': decision['issues'], 'published': 'after' if accepted else 'before',
            'activeModules': after['activeModules'] if accepted else before['activeModules'],
            'cache': {key: decision[key] for key in ('invalidated', 'retained')} if accepted else {
                'invalidated': [], 'retained': sorted(entry['id'] for entry in case['cache']['entries'])},
            'sourceSnapshotsPreserved': original == (assets, case)}