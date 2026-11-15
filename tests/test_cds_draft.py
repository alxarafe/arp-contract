"""Focused draft CDS static checks; not native runtime conformance."""
import sys
import unittest
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import check_cds_draft as c

class CdsDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=c.load_json(ROOT/'fixtures/cds/v1/manifest.json')
        cls.schemas={k:c.load_json(ROOT/v) for k,v in cls.manifest['schemas'].items()}
        cls.docs={k:c.source(ROOT/v) for k,v in cls.manifest['examples'].items()}
        cls.pg=c.source(ROOT/cls.manifest['physicalObservations']['postgresql'])
        cls.mdb=c.source(ROOT/cls.manifest['physicalObservations']['mariadb'])

    def test_fixture_manifest(self):self.assertEqual(c.check(ROOT),10)
    def test_both_engine_shaped_models(self):
        for model in (self.pg,self.mdb):
            with self.subTest(engine=model['source']['dialect']):
                c.validate_document(self.schemas['physical'],model)
                self.assertEqual(c.resolve(model,self.docs['logical'],self.docs['dictionary'],self.docs['public'],self.docs['summary'])['publicFields'],['id','code','rating'])
    def test_child_cannot_restore_parent_exclusion(self):
        altered=deepcopy(self.docs['summary']);altered['fields']=['id','internal_note']
        with self.assertRaisesRegex(c.DraftInvalid,'field expansion'):
            c.resolve(self.mdb,self.docs['logical'],self.docs['dictionary'],self.docs['public'],altered)
    def test_child_cannot_expand_operations(self):
        grandchild={'apiVersion':'arp.projection/v1','id':'demo.items.grandchild',
                    'source':{'projection':'demo.items.summary'},'fields':['id'],
                    'operations':['LIST','GET','DELETE']}
        with self.assertRaisesRegex(c.DraftInvalid,'operation expansion'):
            c.resolve_child(self.docs['summary'],grandchild)
    def test_new_physical_field_not_exposed(self):
        altered=deepcopy(self.mdb);altered['columns'].append({'name':'internal_note','nativeType':'text','scalarType':'TEXT','nullable':True})
        eff=c.resolve(altered,self.docs['logical'],self.docs['dictionary'],self.docs['public'],self.docs['summary'])
        self.assertIn('internal_note',eff['logicalFields']);self.assertNotIn('internal_note',eff['publicFields'])
    def test_reject_logical_vs_physical_conflict(self):
        overlay=deepcopy(self.docs['logical']);overlay['fields']['rating']['constraints']['maximum']='500'
        with self.assertRaisesRegex(c.DraftInvalid,'physical-incompatible'):
            c.resolve(self.mdb,overlay,self.docs['dictionary'],self.docs['public'],self.docs['summary'])
    def test_unknown_operation_not_in_draft_schema(self):
        from jsonschema import ValidationError
        bad=deepcopy(self.docs['public']);bad['operations'].append('EXECUTE')
        with self.assertRaises(ValidationError):c.validate_document(self.schemas['projection'],bad)
    def test_logical_field_not_in_physical_is_rejected(self):
        overlay=deepcopy(self.docs['logical']);overlay['fields']['missing']={'label':'Missing'}
        with self.assertRaisesRegex(c.DraftInvalid,'missing column'):
            c.resolve(self.mdb,overlay,self.docs['dictionary'],self.docs['public'],self.docs['summary'])
    def test_no_duplicate_fields_in_projection(self):
        from jsonschema import ValidationError
        bad=deepcopy(self.docs['summary']);bad['fields'].append('id')
        with self.assertRaises(ValidationError):c.validate_document(self.schemas['projection'],bad)

if __name__=='__main__':unittest.main()
