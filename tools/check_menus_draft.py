#!/usr/bin/env python3
"""Candidate manual/modular menu composition evidence. No renderer or authorization engine."""
from copy import deepcopy

import module_menu_profile as profile
from check_contract import load

ROOT = profile.ROOT


def check():
    assets = load(ROOT / 'fixtures/modules/v1/scenario.json')
    suite = load(ROOT / 'fixtures/menus/v1/cases.json')
    profile.MENU_VALIDATOR.check_schema(profile.MENU_SCHEMA)
    profile.COMPOSITION_VALIDATOR.check_schema(profile.COMPOSITION_SCHEMA)
    ids = [case['id'] for case in suite['cases']]
    assert len(ids) == len(set(ids))
    for case in suite['cases']:
        original = deepcopy((assets, case))
        _, actual = profile.staged(assets, profile.case_host(assets, case['host']))
        assert profile.cds.canonical(actual) == profile.cds.canonical(case['expected']), (case['id'], actual)
        assert original == (assets, case)
    return len(ids)


if __name__ == '__main__':
    print(f'PASS: {check()} menu candidate vectors; no Angular/theme rendering or native conformance')