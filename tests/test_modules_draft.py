"""Composition and selective invalidation properties, without a module loader or cache backend."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_modules_draft as checks
import module_menu_profile as p


class ModuleDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets = p.load(checks.ASSETS)
        suite = p.load(p.ROOT / 'fixtures/modules/v1/transitions.json')
        cls.transitions = {case['id']: case for case in suite['cases']}

    def snapshot(self, **patch):
        return p.activate(self.assets, p.case_host(self.assets, patch))

    def transition(self, identity):
        return p.transition(self.assets, self.transitions[identity])

    def test_shared_module_and_lifecycle_expectations(self):
        self.assertEqual(checks.check(), (31, 17))

    def test_reports_uses_actual_existing_cds_resolution(self):
        snapshot = self.snapshot(active=['reports', 'catalog'])
        self.assertEqual(snapshot['activeModules'], ['catalog', 'reports'])
        projected = {item['id']: item for item in snapshot['cds']['projections']}
        report = projected['reports.articles.summary']
        self.assertEqual(report['source'], {'projection': 'catalog.articles.public'})
        self.assertEqual([field['name'] for field in report['fields']], ['code', 'name'])
        self.assertEqual(report['operations'], ['LIST'])
        self.assertEqual(snapshot['owners'][('logical', 'catalog.articles')], ('module', 'catalog'))
        self.assertEqual(snapshot['owners'][('dictionary', 'app.status')], ('application', 'demo.shop'))

    def test_dependencies_are_not_implicitly_activated_or_cascaded(self):
        rejected = self.snapshot(active=['reports'])
        self.assertFalse(rejected['valid'])
        self.assertEqual(rejected['issues'][0]['code'], 'MODULES_DEPENDENCY_INACTIVE')
        self.assertNotIn('definitions', rejected)
        transition = self.transition('disable-catalog-with-dependent-rejected')
        self.assertEqual(transition['published'], 'before')
        self.assertEqual(transition['activeModules'], ['catalog', 'reports'])
        self.assertEqual(transition['cache']['invalidated'], [])

    def test_deactivation_keeps_host_physical_and_source_inputs_intact(self):
        before = deepcopy(self.assets)
        inactive = self.snapshot(active=[])
        self.assertEqual(set(inactive['definitions']['physical']), {'storage.articles'})
        self.assertNotIn('logical', inactive['definitions'])
        self.assertNotIn('projection', inactive['definitions'])
        self.assertEqual(self.assets, before)
        reactivated = self.snapshot(active=['catalog', 'reports'])
        self.assertEqual(p.module_summary(self.snapshot()), p.module_summary(reactivated))

    def test_application_definition_depending_on_disabled_module_is_not_silently_deleted(self):
        payloads = deepcopy(self.assets['payloads'])
        payloads['own-projection'] = {'apiVersion': 'arp.projection/v1', 'id': 'app.articles',
                                     'source': {'projection': 'catalog.articles.public'},
                                     'fields': ['code'], 'operations': ['LIST']}
        sources = deepcopy(self.assets['applicationSources'])
        sources.append({'providerId': 'application', 'sourceId': 'dependent', 'kind': 'projection',
                        'handle': 'own-projection', 'revision': 'r1'})
        result = self.snapshot(active=[], applicationSources=sources, payloads=payloads)
        self.assertFalse(result['valid'])
        self.assertEqual(result['issues'][0]['code'], 'MODULES_CDS_INVALID')
        self.assertIn('own-projection', payloads)

    def test_source_and_module_enumeration_order_has_no_precedence(self):
        assets = deepcopy(self.assets)
        assets['modules'].reverse()
        assets['applicationSources'].reverse()
        for module in assets['modules']:
            module['sources'].reverse()
        actual = p.activate(assets, p.case_host(assets, {'active': ['reports', 'catalog']}))
        self.assertEqual(p.module_summary(actual), p.module_summary(self.snapshot()))

    def test_dictionary_change_reaches_reports_and_menu_but_not_system(self):
        plan = self.transition('dictionary-change-invalidates-cross-module-derived')['cache']
        self.assertEqual(plan['invalidated'], ['catalog.dictionary', 'catalog.model', 'catalog.public',
                                             'labels.primary.es', 'menu.primary', 'reports.summary'])
        self.assertIn('physical.articles', plan['retained'])
        self.assertIn('app.dictionary', plan['retained'])
        self.assertIn('menu.system', plan['retained'])

    def test_new_contribution_invalidates_preexisting_menu_selection(self):
        cache = self.assets['caches']['catalog']
        self.assertNotIn('reports.summary', {entry['id'] for entry in cache['entries']})
        menu = next(entry for entry in cache['entries'] if entry['id'] == 'menu.primary')
        self.assertIn({'kind': 'selection', 'type': 'menu', 'id': 'app.primary'}, menu['dependsOn'])
        result = self.transition('activate-reports-invalidates-existing-menu-selection')
        self.assertEqual(result['cache']['invalidated'], ['labels.primary.es', 'menu.primary'])
        self.assertIn('catalog.public', result['cache']['retained'])

    def test_translation_and_application_edits_have_different_dependency_closures(self):
        translated = self.transition('translation-change-only-invalidates-label-artifact')['cache']
        self.assertEqual(translated['invalidated'], ['labels.primary.es'])
        edited = self.transition('application-edit-invalidates-only-target-menu')['cache']
        self.assertEqual(edited['invalidated'], ['labels.primary.es', 'menu.primary'])
        self.assertIn('menu.system', edited['retained'])

    def test_context_policy_change_does_not_invalidate_context_free_catalogs(self):
        plan = self.transition('context-change-keeps-context-free-models')['cache']
        self.assertEqual(plan['invalidated'], ['labels.primary.es', 'menu.primary', 'menu.system'])
        self.assertIn('catalog.model', plan['retained'])
        self.assertIn('reports.summary', plan['retained'])

    def test_cache_graph_scope_and_no_change(self):
        self.assertEqual(self.transition('no-change-retains-entire-general-cache')['cache']['invalidated'], [])
        self.assertEqual(self.transition('cache-scope-isolation')['issues'][0]['code'], 'MODULES_CACHE_SCOPE')
        self.assertEqual(self.transition('cache-cycle-rejected')['issues'][0]['code'], 'MODULES_CACHE_GRAPH')

    def test_unproven_dependency_completeness_is_conservative(self):
        case = deepcopy(self.transitions['unknown-dependency-completeness-invalidates-conservatively'])
        del case['cache']['entries'][-1]['complete']
        result = p.transition(self.assets, case)
        self.assertIn('uncertain.extension', result['cache']['invalidated'])

    def test_negative_definition_lookup_is_a_dependency(self):
        before, menus = p.staged(self.assets, p.case_host(self.assets, {}))
        self.assertTrue(menus['valid'])
        payloads = deepcopy(self.assets['payloads'])
        payloads['new-extension'] = [{'id': 'app.newNote'}]
        sources = deepcopy(self.assets['applicationSources'])
        sources.append({'providerId': 'application', 'sourceId': 'new-note', 'kind': 'custom.note',
                        'handle': 'new-extension', 'revision': 'r1'})
        host = p.case_host(self.assets, {'payloads': payloads, 'applicationSources': sources})
        after, _ = p.staged(self.assets, host)
        cache = {'applicationId': 'demo.shop', 'entries': [{'id': 'negative.lookup', 'complete': True,
                 'dependsOn': [{'kind': 'selection', 'type': 'custom.note', 'id': 'app.newNote'}]}]}
        self.assertEqual(p.cache_plan(before, after, cache)['invalidated'], ['negative.lookup'])

    def test_active_target_does_not_excuse_undeclared_projection_dependency(self):
        modules = deepcopy(self.assets['modules'])
        modules[1]['dependencies'] = []
        result = self.snapshot(modules=modules)
        self.assertEqual(result['issues'][0]['code'], 'MODULES_DEPENDENCY_UNDECLARED')
        self.assertNotIn('definitions', result)

    def test_reference_owner_is_not_inferred_from_identifier_prefix(self):
        cases = p.load(p.ROOT / 'fixtures/modules/v1/cases.json')['cases']
        case = deepcopy(next(c for c in cases if c['id'] == 'logical-binding-requires-dictionary-owner'))
        case['host']['payloads']['vocabulary-dictionary']['elements'][0]['id'] = 'shared.code'
        case['host']['payloads']['catalog-logical']['fields']['code']['dictionary'] = 'shared.code'
        result = p.activate(self.assets, p.case_host(self.assets, case['host']))
        self.assertEqual(result['issues'][0]['code'], 'MODULES_DEPENDENCY_UNDECLARED')
        case['host']['modules'][0]['dependencies'] = ['vocabulary']
        result = p.activate(self.assets, p.case_host(self.assets, case['host']))
        self.assertTrue(result['valid'])
        self.assertEqual(result['owners'][('dictionary', 'shared.code')], ('module', 'vocabulary'))

    def test_transitive_activation_does_not_replace_direct_reference_declaration(self):
        modules = deepcopy(self.assets['modules'])
        modules[1]['dependencies'] = ['bridge']
        modules.append({'apiVersion': 'arp.module/v1', 'id': 'bridge', 'dependencies': ['catalog'], 'sources': []})
        result = self.snapshot(modules=modules, active=['catalog', 'reports', 'bridge'])
        self.assertEqual(result['issues'][0]['code'], 'MODULES_DEPENDENCY_UNDECLARED')
        modules[1]['dependencies'].append('catalog')
        self.assertTrue(self.snapshot(modules=modules, active=['catalog', 'reports', 'bridge'])['valid'])

    def test_menu_ownership_checks_are_not_masked_by_application_override(self):
        payloads = deepcopy(self.assets['payloads'])
        entry = payloads['catalog-menus']['contributions'][0]['entries'][0]
        entry['destination']['target'] = 'reports.articles.summary'
        composition = {'apiVersion': 'arp.menu-composition/v1', 'edits': [
            {'menu': 'app.primary', 'entry': 'catalog.articles', 'changes': {
                'destination': {'kind': 'route', 'target': 'app.home'}}}]}
        _, result = p.staged(self.assets, p.case_host(self.assets, {
            'payloads': payloads, 'composition': composition}))
        self.assertEqual(result['issues'][0]['code'], 'MODULES_DEPENDENCY_UNDECLARED')

    def test_registered_extension_reports_typed_mandatory_references(self):
        cases = {c['id']: c for c in p.load(p.ROOT / 'fixtures/modules/v1/cases.json')['cases']}
        for name in ('extension-processor-mandatory-reference-requires-owner',
                     'extension-processor-reference-with-declaration',
                     'extension-processor-missing-reference-rejected'):
            case = cases[name]
            result = p.module_summary(p.activate(self.assets, p.case_host(self.assets, case['host'])))
            self.assertEqual(p.cds.canonical(result), p.cds.canonical(case['expected']))
        case = deepcopy(cases['extension-processor-mandatory-reference-requires-owner'])
        case['host'].pop('processorReferences')
        case['host']['payloads']['insights-note'][0]['fixtureText'] = 'catalog.code is only literal text'
        self.assertTrue(p.activate(self.assets, p.case_host(self.assets, case['host']))['valid'])

    def test_translation_processor_reports_known_label_owner(self):
        payloads = deepcopy(self.assets['payloads'])
        payloads['catalog-menus']['contributions'][0]['entries'][0]['labelKey'] = 'reports.menu.summary'
        _, result = p.staged(self.assets, p.case_host(self.assets, {'payloads': payloads}))
        self.assertEqual(result['issues'][0]['code'], 'MODULES_DEPENDENCY_UNDECLARED')

    def test_failed_dependency_check_preserves_previous_publication_and_cache(self):
        result = self.transition('undeclared-definition-dependency-rejects-whole-plan')
        self.assertFalse(result['valid'])
        self.assertEqual(result['published'], 'before')
        self.assertEqual(result['cache']['invalidated'], [])
        self.assertEqual(result['activeModules'], ['catalog', 'reports'])

    def test_operation_permissions_are_part_of_context_cache_evidence(self):
        result = self.transition('operation-access-change-invalidates-context-menus')
        self.assertEqual(result['cache']['invalidated'], ['labels.primary.es', 'menu.primary', 'menu.system'])
        self.assertIn('catalog.public', result['cache']['retained'])
        self.assertIn('reports.summary', result['cache']['retained'])

    def test_empty_source_changes_menu_selection_not_module_or_projection(self):
        result = self.transition('empty-source-retires-only-its-menu-contribution')
        self.assertEqual(result['activeModules'], ['catalog', 'reports'])
        self.assertEqual(result['cache']['invalidated'], ['labels.primary.es', 'menu.primary'])
        self.assertIn('reports.summary', result['cache']['retained'])

    def test_limits_and_invalid_request_shape_fail_before_publication(self):
        self.assertFalse(self.snapshot(active=None)['valid'])
        self.assertEqual(self.snapshot(modules=self.assets['modules'] * 129)['issues'][0]['code'], 'MODULES_LIMIT')
        sources = deepcopy(self.assets['applicationSources'])
        del sources[0]['providerId']
        self.assertEqual(self.snapshot(applicationSources=sources)['issues'][0]['code'], 'MODULES_SCHEMA_INVALID')

    def test_menu_conflict_rejects_whole_candidate_not_just_menu_cache(self):
        result = self.transition('menu-conflict-does-not-publish-module-plan')
        self.assertFalse(result['valid'])
        self.assertEqual(result['published'], 'before')
        self.assertEqual(result['cache']['invalidated'], [])
        self.assertTrue(result['sourceSnapshotsPreserved'])


if __name__ == '__main__':
    unittest.main()