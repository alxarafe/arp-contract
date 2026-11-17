"""Manual/modular menu properties. Host visibility is private evidence, not a permission language."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_menus_draft as checks
import module_menu_profile as p


class MenuDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets = p.load(p.ROOT / 'fixtures/modules/v1/scenario.json')

    def compose(self, **patch):
        return p.staged(self.assets, p.case_host(self.assets, patch))[1]

    @staticmethod
    def primary(result):
        return next(menu for menu in result['menus'] if menu['id'] == 'app.primary')['entries']

    def test_all_shared_menu_expectations(self):
        self.assertEqual(checks.check(), 35)

    def test_manual_menus_work_without_any_active_module(self):
        result = self.compose(active=[])
        self.assertTrue(result['valid'])
        self.assertEqual([entry['id'] for entry in self.primary(result)], ['app.home'])
        self.assertEqual({menu['scope'] for menu in result['menus']},
                         {'primary', 'secondary', 'contextual', 'system', 'workspace'})

    def test_manual_navigation_needs_no_dictionary_or_cds_source(self):
        sources = [source for source in self.assets['applicationSources'] if source['kind'] == 'menu']
        snapshot, result = p.staged(self.assets, p.case_host(self.assets, {
            'active': [], 'applicationSources': sources, 'registeredKinds': ['menu']}))
        self.assertTrue(result['valid'])
        self.assertEqual(snapshot['definitions'], {})
        self.assertEqual([entry['id'] for entry in self.primary(result)], ['app.home'])

    def test_shared_contributions_use_one_tree(self):
        entries = self.primary(self.compose())
        self.assertEqual([entry['id'] for entry in entries], ['app.home', 'app.business'])
        self.assertEqual([entry['id'] for entry in entries[1]['children']], ['catalog.articles', 'reports.summary'])

    def test_equal_order_uses_id_not_source_load_order_or_labels(self):
        composition = {'apiVersion': 'arp.menu-composition/v1', 'edits': [
            {'menu': 'app.primary', 'entry': name, 'changes': {'order': 5}}
            for name in ('reports.summary', 'catalog.articles')]}
        children = self.primary(self.compose(composition=composition))[1]['children']
        self.assertEqual([entry['id'] for entry in children], ['catalog.articles', 'reports.summary'])

    def test_multiple_menus_may_share_scope_and_entries_may_share_ids_across_menus(self):
        payloads = deepcopy(self.assets['payloads'])
        payloads['app-menus']['menus'].append({'id': 'app.primary.other', 'scope': 'primary', 'entries': [
            {'id': 'catalog.articles', 'label': 'Acceso alternativo',
             'destination': {'kind': 'route', 'target': 'app.home'}}]})
        result = self.compose(payloads=payloads)
        self.assertTrue(result['valid'])
        self.assertEqual(sum(menu['scope'] == 'primary' for menu in result['menus']), 2)

    def test_optional_customization_survives_deactivation_and_reapplies(self):
        composition = {'apiVersion': 'arp.menu-composition/v1', 'edits': [
            {'menu': 'app.primary', 'entry': 'reports.summary', 'whenMissing': 'ignore', 'changes': {'order': 5}}]}
        before = deepcopy(composition)
        off = self.compose(active=['catalog'], composition=composition)
        on = self.compose(composition=composition)
        self.assertEqual([x['id'] for x in self.primary(off)[1]['children']], ['catalog.articles'])
        self.assertEqual([x['id'] for x in self.primary(on)[1]['children']], ['reports.summary', 'catalog.articles'])
        self.assertEqual(composition, before)

    def test_reparent_before_exclusion_is_explicit_not_automatic_promotion(self):
        composition = {'apiVersion': 'arp.menu-composition/v1', 'edits': [
            {'menu': 'app.primary', 'entry': 'reports.summary', 'changes': {'parent': None, 'order': 5}},
            {'menu': 'app.primary', 'entry': 'app.business', 'exclude': True}]}
        self.assertEqual([entry['id'] for entry in self.primary(self.compose(composition=composition))],
                         ['app.home', 'reports.summary'])

    def test_denied_parent_hides_subtree_even_if_child_destination_is_available(self):
        payloads = deepcopy(self.assets['payloads'])
        payloads['app-menus']['menus'][0]['entries'].append({'id': 'app.home.child', 'parent': 'app.home',
            'label': 'Detalle', 'destination': {'kind': 'route', 'target': 'app.details'}})
        allowed = [x for x in self.assets['defaults']['allowedDestinations'] if x != 'route:app.home']
        entries = self.primary(self.compose(payloads=payloads, allowedDestinations=allowed))
        self.assertEqual([entry['id'] for entry in entries], ['app.business'])

    def test_inactive_projection_referenced_by_application_is_not_silently_hidden(self):
        payloads = deepcopy(self.assets['payloads'])
        payloads['app-menus']['menus'][0]['entries'].append({'id': 'app.report', 'label': 'Informe',
            'destination': {'kind': 'projection', 'target': 'reports.articles.summary', 'operation': 'LIST'}})
        result = self.compose(active=['catalog'], payloads=payloads)
        self.assertFalse(result['valid'])
        self.assertEqual(result['issues'][0]['code'], 'MENUS_TARGET_MISSING')

    def test_application_destination_override_does_not_expand_projection_operations(self):
        composition = {'apiVersion': 'arp.menu-composition/v1', 'edits': [
            {'menu': 'app.primary', 'entry': 'reports.summary', 'changes': {
                'destination': {'kind': 'projection', 'target': 'reports.articles.summary', 'operation': 'GET'}}}]}
        result = self.compose(composition=composition)
        self.assertEqual(result['issues'][0]['code'], 'MENUS_OPERATION_UNAVAILABLE')

    def test_order_is_a_json_mathematical_integer_not_boolean(self):
        composition = {'apiVersion': 'arp.menu-composition/v1', 'edits': [
            {'menu': 'app.primary', 'entry': 'catalog.articles', 'changes': {'order': True}}]}
        self.assertEqual(self.compose(composition=composition)['issues'][0]['code'], 'MENUS_COMPOSITION_INVALID')

    def test_hierarchy_limit_and_no_partial_result(self):
        payloads = deepcopy(self.assets['payloads'])
        entries = [{'id': 'node.n' + str(i), 'label': 'Grupo', 'parent': 'node.n' + str(i - 1)}
                   for i in range(65)]
        entries[0]['parent'] = None
        payloads['app-menus']['menus'][0]['entries'] = entries
        result = self.compose(active=[], payloads=payloads)
        self.assertFalse(result['valid'])
        self.assertEqual(result['issues'][0]['code'], 'MENUS_LIMIT')
        self.assertNotIn('menus', result)

    def test_no_model_or_crud_generates_a_menu(self):
        modules = deepcopy(self.assets['modules'])
        for module in modules:
            module['sources'] = [source for source in module['sources'] if source['kind'] != 'menu']
        self.assertEqual([entry['id'] for entry in self.primary(self.compose(modules=modules))], ['app.home'])

    def test_two_main_options_keep_one_functional_hierarchy(self):
        cases = p.load(p.ROOT / 'fixtures/menus/v1/cases.json')['cases']
        case = next(c for c in cases if c['id'] == 'two-primary-options-one-functional-hierarchy')
        result = self.compose(**case['host'])
        before = deepcopy(result)
        roots = {entry['id']: entry for entry in self.primary(result)}
        self.assertEqual(list(roots), ['app.catalog', 'app.reports'])
        # A theme may show either selection's descendants in another visual region; no new functional menu.
        self.assertEqual([e['id'] for e in roots['app.catalog']['children']], ['catalog.articles'])
        self.assertEqual([e['id'] for e in roots['app.reports']['children']], ['reports.summary'])
        self.assertEqual(sum(menu['scope'] == 'primary' for menu in result['menus']), 1)
        self.assertEqual(result, before)

    def test_list_allowed_get_denied_is_not_projection_wide_authorization(self):
        cases = p.load(p.ROOT / 'fixtures/menus/v1/cases.json')['cases']
        case = next(c for c in cases if c['id'] == 'list-authorized-get-denied-same-projection')
        snapshot, result = p.staged(self.assets, p.case_host(self.assets, case['host']))
        declared = next(pr for pr in snapshot['cds']['projections'] if pr['id'] == 'catalog.articles.public')
        self.assertIn('GET', declared['operations'])
        self.assertIn('GET', self.assets['defaults']['projectionAccess'][declared['id']]['available'])
        children = self.primary(result)[1]['children']
        operations = [entry['destination']['operation'] for entry in children
                      if entry['destination']['target'] == declared['id']]
        self.assertEqual(operations, ['LIST'])
        access = deepcopy(self.assets['defaults']['projectionAccess'])
        access[declared['id']]['authorized'].append('GET')
        allowed = self.compose(**case['host'], projectionAccess=access)
        self.assertIn('catalog.details', [e['id'] for e in self.primary(allowed)[1]['children']])
        access[declared['id']]['authorized'] = []
        denied = self.compose(**case['host'], projectionAccess=access)
        self.assertFalse(any(e['destination']['target'] == declared['id']
                             for e in self.primary(denied)[1]['children']))

    def test_authorized_but_unavailable_operation_is_not_exposed(self):
        cases = p.load(p.ROOT / 'fixtures/menus/v1/cases.json')['cases']
        case = next(c for c in cases if c['id'] == 'get-authorized-but-runtime-unavailable')
        self.assertIn('GET', case['host']['projectionAccess']['catalog.articles.public']['authorized'])
        result = self.compose(**case['host'])
        self.assertNotIn('catalog.details', [e['id'] for e in self.primary(result)[1]['children']])

    def test_empty_source_forms_are_valid_equivalent_and_do_not_create_a_menu(self):
        forms = [{'apiVersion': 'arp.menu/v1'}, {'apiVersion': 'arp.menu/v1', 'menus': [], 'contributions': []}]
        results = []
        for form in forms:
            self.assertTrue(p.MENU_VALIDATOR.is_valid(form))
            payloads = deepcopy(self.assets['payloads'])
            payloads['reports-menus'] = form
            results.append(self.compose(payloads=payloads))
        self.assertEqual(results[0], results[1])
        self.assertEqual([e['id'] for e in self.primary(results[0])[1]['children']], ['catalog.articles'])
        payloads['app-menus'] = forms[0]
        self.assertEqual(self.compose(payloads=payloads)['issues'][0]['code'], 'MENUS_MENU_MISSING')
        self.assertEqual(self.compose(active=[], payloads=payloads), {'valid': True, 'issues': [], 'menus': []})

    def test_declared_empty_menu_remains_distinct_from_empty_source(self):
        cases = p.load(p.ROOT / 'fixtures/menus/v1/cases.json')['cases']
        case = next(c for c in cases if c['id'] == 'declared-empty-menu-is-admissible')
        result = self.compose(**case['host'])
        empty = next(menu for menu in result['menus'] if menu['id'] == 'app.empty')
        self.assertEqual(empty, {'id': 'app.empty', 'scope': 'custom', 'entries': []})

    def test_contextual_scope_has_no_record_selection_dynamic_actions_or_visual_conditions(self):
        for field, value in [('recordKey', 'row-42'), ('condition', 'selected == true'), ('dynamicActions', [])]:
            payloads = deepcopy(self.assets['payloads'])
            contextual = next(menu for menu in payloads['app-menus']['menus'] if menu['scope'] == 'contextual')
            contextual['entries'][0][field] = value
            result = self.compose(payloads=payloads)
            self.assertEqual(result['issues'][0]['code'], 'MODULES_SOURCE_INVALID')
            self.assertNotIn('menus', result)

    def test_source_enumeration_does_not_change_composition(self):
        assets = deepcopy(self.assets)
        assets['modules'].reverse()
        assets['applicationSources'].reverse()
        for module in assets['modules']:
            module['sources'].reverse()
        result = p.staged(assets, p.case_host(assets, {}))[1]
        self.assertEqual(p.cds.canonical(result), p.cds.canonical(self.compose()))


if __name__ == '__main__':
    unittest.main()