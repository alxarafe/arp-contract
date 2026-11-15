#!/usr/bin/env python3
"""ARP-CDS-001 DRAFT fixture/schema integrity checker; NOT a production ARP runtime.

This checks only draft examples, source shapes and a deliberately small subset of
semantic invariants. It neither implements the portable YAML profile nor queries DBs.
"""
import json
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from jsonschema import Draft202012Validator
import yaml

ROOT = Path(__file__).resolve().parents[1]

class DraftInvalid(AssertionError):
    pass

class NoDuplicates(yaml.SafeLoader):
    pass

def strict_mapping(loader, node):
    loader.flatten_mapping(node)
    result = {}
    for key, value in node.value:
        k = loader.construct_object(key, deep=True)
        if k in result:
            raise DraftInvalid(f'duplicate YAML key: {k!r}')
        result[k] = loader.construct_object(value, deep=True)
    return result

NoDuplicates.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, strict_mapping)

def source(path):
    raw=path.read_text(encoding='utf-8')
    # Development fixture loader, not a normative runtime intake profile.
    for event in yaml.parse(raw):
        if isinstance(event, yaml.events.AliasEvent) or getattr(event,'anchor',None):
            raise DraftInvalid(f'aliases/anchors forbidden in demo source: {path}')
    return yaml.load(raw,Loader=NoDuplicates)

def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))

def validate_document(schema,document):
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(document)

def expect(condition, message):
    if not condition:
        raise DraftInvalid(message)

def resolve_child(parent, child):
    """Proposed monotonic projection reduction; no retrieval of excluded fields/ops."""
    expect(child['source']=={'projection':parent['id']}, 'child source mismatch')
    expect(set(child['fields'])<=set(parent['fields']), 'definition-invalid: field expansion')
    expect(set(child['operations'])<=set(parent['operations']), 'definition-invalid: operation expansion')


def resolve(model, logical, dictionary, public, summary):
    """Only checks proposed demo invariants, not a complete runtime resolver."""
    physical_names=[c['name'] for c in model['columns']]
    expect(len(physical_names)==len(set(physical_names)), 'duplicate physical column')
    expect(logical['physical']==model['id']==logical['id'], 'incorrect physical reference')
    expect(set(logical['fields'])<=set(physical_names), 'overlay references missing column')
    elements={e['id']:e for e in dictionary['elements']}
    expect(len(elements)==len(dictionary['elements']), 'duplicate dictionary ID')
    for field, overlay in logical['fields'].items():
        if 'dictionary' in overlay:
            expect(overlay['dictionary'] in elements,'dictionary ref unresolved')
            physical=next(c for c in model['columns'] if c['name']==field)
            expect(elements[overlay['dictionary']]['type']==physical.get('scalarType'), 'dictionary type incompatible')
        c=overlay.get('constraints',{})
        if 'minimum' in c and 'maximum' in c:
            expect(Decimal(c['minimum'])<=Decimal(c['maximum']), 'ill-formed interval')
        physical=next(col for col in model['columns'] if col['name']==field)
        for boundary in ('minimum','maximum'):
            if boundary in c and boundary in physical:
                lv,pv=Decimal(c[boundary]),Decimal(physical[boundary])
                expect(lv>=pv if boundary=='minimum' else lv<=pv,
                       f'physical-incompatible: {field}.{boundary}')
    expect(public['source']=={'entity':logical['id']},'public projection source mismatch')
    expect(set(public['fields'])<=set(physical_names),'public references unrecognized column')
    resolve_child(public,summary)
    return {'logicalFields':physical_names,'publicFields':public['fields'],'summaryFields':summary['fields']}

def check(root=ROOT):
    m=load_json(root/'fixtures/cds/v1/manifest.json')
    expect(m['feature']=='ARP-CDS-001' and m['status']=='unreleased-draft', 'manifest not draft')
    schema={key:load_json(root/path) for key,path in m['schemas'].items()}
    docs={key:source(root/path) for key,path in m['examples'].items()}
    for key in ('logical','public','summary'):
        validate_document(schema['logical'] if key=='logical' else schema['projection'],docs[key])
    expect(docs['dictionary']['apiVersion']=='arp.dictionary/v1', 'dictionary contract ref')
    observations={k:source(root/path) for k,path in m['physicalObservations'].items()}
    for physical in observations.values():
        validate_document(schema['physical'],physical)
    ids=[]
    for case in m['scenarios']:
        ids.append(case['id']);cid=case['id'];engine=case.get('engine','mariadb')
        physical=deepcopy(observations[engine]); logical=deepcopy(docs['logical'])
        public=deepcopy(docs['public']);summary=deepcopy(docs['summary'])
        change=case.get('mutation',{})
        if 'appendPhysicalColumn' in change:
            physical['columns'].append(change['appendPhysicalColumn'])
            validate_document(schema['physical'],physical)
        if 'summaryFields' in change:summary['fields']=change['summaryFields']
        if 'summaryOperations' in change:
            summary['operations']=change['summaryOperations']
        if 'ratingMaximum' in change:
            logical['fields']['rating']['constraints']['maximum']=change['ratingMaximum']
        if 'removePhysicalMaximum' in change:
            for col in physical['columns']:
                if col['name']==change['removePhysicalMaximum']:
                    col.pop('maximum',None)
        if cid=='derived-cannot-expand-operations':
            grandchild={'id':'demo.items.grandchild','source':{'projection':summary['id']},
                        'fields':['id'],'operations':change['grandchildOperations'],
                        'apiVersion':'arp.projection/v1'}
            validate_document(schema['projection'],grandchild)
            try:resolve_child(summary,grandchild)
            except DraftInvalid as e:expect('operation expansion' in str(e),'wrong negative family')
            else:raise DraftInvalid('grandchild operation expansion accepted')
            continue
        if cid=='unknown-operation-identifier':
            expect(not Draft202012Validator(schema['projection']).is_valid(summary),
                   'unknown operation unexpectedly valid')
            continue
        if cid=='derived-cannot-expand-fields':
            try:resolve(physical,logical,docs['dictionary'],public,summary)
            except DraftInvalid as e:expect('definition-invalid' in str(e),'wrong negative family')
            else:raise DraftInvalid('field expansion accepted')
            continue
        if cid=='physical-capacity-conflict':
            try:resolve(physical,logical,docs['dictionary'],public,summary)
            except DraftInvalid as e:expect('physical-incompatible' in str(e),'wrong negative family')
            else:raise DraftInvalid('physical conflict accepted')
            continue
        outcome=resolve(physical,logical,docs['dictionary'],public,summary)
        if cid=='rating-out-of-logical-range':
            val=Decimal(case['input']['rating']);c=logical['fields']['rating']['constraints']
            expect(val>Decimal(c['maximum']) or val<Decimal(c['minimum']), 'data not invalid')
        elif cid=='module-disabled':
            expect(change['moduleEnabled'] is False,'module case has no disablement')
            expect(case['expected']=={'serviceExposed':False,'userFilesPreserved':True}, 'incorrect disabled expectation')
        elif cid=='unknown-physical-capacity':
            expect('maximum' not in next(x for x in physical['columns'] if x['name']=='rating'), 'maximum not removed')
            expect(case['expected']['capacityStatus']=='not-verified', 'unknown must not be compatible')
        else:
            for prop,val in case['expected'].items():
                if prop=='ratingType':
                    expect(next(x for x in physical['columns'] if x['name']=='rating')['scalarType']==val,'rating type mismatch')
                else:expect(outcome[prop]==val, f'{cid}: {prop} mismatch')
    expect(len(ids)==len(set(ids)), 'duplicate scenario ID')
    return len(ids)

if __name__=='__main__':
    n=check();print(f'PASS: 3 draft schemas, 2 physical observations, {n} fixture scenarios (STATIC ONLY; no runtime conformance)')
