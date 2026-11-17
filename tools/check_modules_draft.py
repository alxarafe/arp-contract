#!/usr/bin/env python3
"""Candidate module composition and shared-cache invalidation evidence. Pure fixtures only."""
from copy import deepcopy

import module_menu_profile as profile
from check_contract import load

ROOT = profile.ROOT
ASSETS = ROOT / 'fixtures/modules/v1/scenario.json'


def check():
    assets = load(ASSETS)
    cases = load(ROOT / 'fixtures/modules/v1/cases.json')
    transitions = load(ROOT / 'fixtures/modules/v1/transitions.json')
    profile.MODULE_VALIDATOR.check_schema(profile.MODULE_SCHEMA)
    for suite in (cases, transitions):
        ids = [case['id'] for case in suite['cases']]
        assert len(ids) == len(set(ids))
    for case in cases['cases']:
        original = deepcopy((assets, case))
        snapshot, menus = profile.staged(assets, profile.case_host(assets, case['host']))
        actual = profile.module_summary(snapshot) if menus['valid'] else menus
        assert profile.cds.canonical(actual) == profile.cds.canonical(case['expected']), case['id']
        assert original == (assets, case)
    for case in transitions['cases']:
        actual = profile.transition(assets, case)
        assert profile.cds.canonical(actual) == profile.cds.canonical(case['expected']), (case['id'], actual)
    return len(cases['cases']), len(transitions['cases'])


if __name__ == '__main__':
    counts = check()
    print(f'PASS: {counts[0]} module + {counts[1]} lifecycle/cache candidate vectors; no installer or cache backend')