"""Small fail-closed registry. A profile describes evidence, not a generic flash ABI."""
import json
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent
NAMES = ('dac960pg', 'accele160')
WORKFLOWS = ('firmware_romhook', 'firmware_one_shot', 'firmware_flashimage',
             'rtems_legacy', 'rtems_accele160', 'doom_i960')


def load(name):
    if name not in NAMES:
        raise ValueError(f'unknown card profile: {name}')
    data = json.loads((DIRECTORY / (name + '.json')).read_text())
    if data.get('schema') != 1 or data.get('id') != name:
        raise ValueError(f'invalid card profile header: {name}')
    if set(data.get('workflows', {})) != set(WORKFLOWS):
        raise ValueError(f'incomplete card workflow declaration: {name}')
    if not all(type(value) is bool for value in data['workflows'].values()):
        raise ValueError(f'invalid workflow declaration: {name}')
    ids = data.get('pci_ids', [])
    if len(ids) != 4 or any(not isinstance(x, str) or len(x) != 4 or
                            any(c not in '0123456789abcdef' for c in x) for x in ids):
        raise ValueError(f'invalid PCI identity: {name}')
    if data.get('doom', {}).get('clock') not in ('dac960pg_timer0', 'accele160_timer1'):
        raise ValueError(f'invalid Doom clock: {name}')
    return data


def require_workflow(name, workflow):
    profile = load(name)
    if workflow not in WORKFLOWS or not profile['workflows'][workflow]:
        raise ValueError(f'{workflow} is not qualified for {name}')
    return profile


def pci_ids(name):
    return tuple(int(x, 16) for x in load(name)['pci_ids'])
