"""Offline, bilingual, partial sing-box configuration linting. Python 3.10+."""
import argparse
import json
import sys
from pathlib import Path

MESSAGES = {
    'json': ('Invalid JSON or duplicate object keys.', 'JSON ပုံစံမှားနေသည် သို့မဟုတ် key ထပ်နေသည်။'),
    'shape': ('Expected an object or list of objects at this location.', 'ဤနေရာတွင် object သို့မဟုတ် object စာရင်း လိုအပ်သည်။'),
    'tag': ('Tag must be a nonempty string and unique in its namespace.', 'Tag သည် စာသားဖြစ်ရမည်၊ အလွတ်မဖြစ်ရ၊ သက်ဆိုင်ရာအုပ်စုအတွင်း မထပ်ရပါ။'),
    'reference': ('Referenced outbound/endpoint tag does not exist or is not a string.', 'ညွှန်းထားသော outbound/endpoint tag မရှိပါ သို့မဟုတ် စာသားမဟုတ်ပါ။'),
    'port': ('Port must be an integer from 1 to 65535.', 'Port သည် ၁ မှ ၆၅၅၃၅ အတွင်း ကိန်းပြည့်ဖြစ်ရမည်။'),
    'members': ('Expected a nonempty list of outbound tags.', 'Outbound tag စာရင်း လိုအပ်ပြီး အလွတ်မဖြစ်ရပါ။'),
    'default': ('Selector default must be one of its members.', 'Selector default သည် ၎င်း၏စာရင်းထဲမှ tag ဖြစ်ရမည်။'),
    'read': ('Cannot read UTF-8 input file.', 'UTF-8 ဖိုင်ကို ဖတ်မရပါ။'),
}


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('non-JSON number')


def lint(text):
    """Return safe issue codes and fixed schema locations, never input values."""
    issues = []
    def issue(code, location):
        issues.append({'code': code, 'location': location})
    try:
        data = json.loads(text, object_pairs_hook=strict_object, parse_constant=reject_constant)
    except (ValueError, RecursionError):
        return [{'code': 'json', 'location': '$'}]
    if not isinstance(data, dict):
        return [{'code': 'shape', 'location': '$'}]

    groups = {}
    namespaces = {'inbounds': set(), 'outbounds': set(), 'endpoints': set()}
    for group in namespaces:
        items = data.get(group, [])
        if not isinstance(items, list):
            issue('shape', group)
            items = []
        groups[group] = items
        for i, item in enumerate(items):
            location = f'{group}[{i}]'
            if not isinstance(item, dict):
                issue('shape', location)
                continue
            if 'tag' in item:
                tag = item['tag']
                if not isinstance(tag, str) or not tag or tag in namespaces[group]:
                    issue('tag', location + '.tag')
                else:
                    namespaces[group].add(tag)
            for key in ('server_port', 'listen_port'):
                if key in item and (type(item[key]) is not int or not 1 <= item[key] <= 65535):
                    issue('port', location + '.' + key)
    for i, item in enumerate(groups['endpoints']):
        if isinstance(item, dict) and isinstance(item.get('tag'), str) and item['tag'] in namespaces['outbounds']:
            issue('tag', f'endpoints[{i}].tag')
    targets = namespaces['outbounds'] | namespaces['endpoints']

    def reference(value, location):
        if not isinstance(value, str) or value not in targets:
            issue('reference', location)

    for group in ('outbounds', 'endpoints'):
        for i, item in enumerate(groups[group]):
            if not isinstance(item, dict):
                continue
            location = f'{group}[{i}]'
            if item.get('detour') not in (None, ''):
                reference(item['detour'], location + '.detour')
            if item.get('type') in ('selector', 'urltest'):
                members = item.get('outbounds')
                if not isinstance(members, list) or not members:
                    issue('members', location + '.outbounds')
                else:
                    for j, member in enumerate(members):
                        reference(member, location + f'.outbounds[{j}]')
                    if item.get('type') == 'selector' and item.get('default') not in (None, '') and item['default'] not in members:
                        issue('default', location + '.default')
    route = data.get('route', {})
    if not isinstance(route, dict):
        issue('shape', 'route')
    else:
        if route.get('final') not in (None, ''):
            reference(route['final'], 'route.final')
        pending = [(route.get('rules', []), 'route.rules')]
        while pending:
            rules, location = pending.pop()
            if not isinstance(rules, list):
                issue('shape', location)
                continue
            for i, rule in enumerate(rules):
                here = f'{location}[{i}]'
                if not isinstance(rule, dict):
                    issue('shape', here)
                    continue
                if 'outbound' in rule:
                    reference(rule['outbound'], here + '.outbound')
                if 'rules' in rule:
                    pending.append((rule['rules'], here + '.rules'))
    return issues


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    parser.add_argument('--lang', choices=['en', 'my'], default='en')
    parser.add_argument('--json', action='store_true', dest='json_output')
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        issues = lint(args.file.read_text(encoding='utf-8-sig'))
        status = 1 if issues else 0
    except (OSError, UnicodeError):
        issues = [{'code': 'read', 'location': '$'}]
        status = 2
    for item in issues:
        item['message'] = MESSAGES[item['code']][args.lang == 'my']
    if args.json_output:
        print(json.dumps({'issues': issues, 'scope': 'partial-static-check'}, ensure_ascii=False))
    elif issues:
        for item in issues:
            print(f"{item['location']}: [{item['code']}] {item['message']}")
    else:
        print('စစ်ဆေးထားသောအပိုင်းတွင် အမှားမတွေ့ပါ။ sing-box check ဖြင့် ဆက်စစ်ပါ။' if args.lang == 'my' else 'No issues in supported checks. Also run sing-box check with your installed version.')
    return status


if __name__ == '__main__':
    sys.exit(main())
