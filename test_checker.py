import json
import subprocess
import sys
import unittest
from pathlib import Path
from vpn_config_check import lint

ROOT = Path(__file__).resolve().parents[1]


class CheckerTests(unittest.TestCase):
    def test_example(self):
        self.assertEqual(lint((ROOT / 'examples/basic.json').read_text()), [])

    def test_duplicate_and_nonstandard_json(self):
        for text in ('{"password":"SECRET","password":"HIDDEN"}', '{"x":NaN}', '[]', '{'):
            with self.subTest(text=text):
                self.assertTrue(lint(text))
                self.assertNotIn('SECRET', str(lint(text)))

    def test_bad_shapes_never_crash(self):
        for value in (None, 42, 'bad', {}, [None, 4, 'bad']):
            for key in ('inbounds', 'outbounds', 'endpoints', 'route'):
                with self.subTest(value=value, key=key):
                    lint(json.dumps({key: value}))

    def test_references_and_ports(self):
        config = {'outbounds': [{'type': 'selector', 'tag': 'pick', 'outbounds': ['absent'], 'default': 'other'}, {'tag': 'pick', 'server_port': True}], 'route': {'rules': [{'rules': [{'outbound': 'missing'}]}]}}
        codes = [x['code'] for x in lint(json.dumps(config))]
        self.assertEqual(codes.count('reference'), 2)
        self.assertIn('tag', codes)
        self.assertIn('port', codes)
        self.assertIn('default', codes)

    def test_endpoint_reference(self):
        self.assertEqual(lint(json.dumps({'endpoints': [{'tag': 'wg'}], 'route': {'final': 'wg'}})), [])

    def test_credentials_not_echoed(self):
        config = {'outbounds': [{'tag': 'SECRET', 'server_port': 'SECRET', 'password': 'SECRET', 'detour': 'SECRET-MISSING'}]}
        self.assertNotIn('SECRET', str(lint(json.dumps(config))))

    def test_cli(self):
        result = subprocess.run([sys.executable, str(ROOT / 'vpn_config_check.py'), str(ROOT / 'examples/basic.json'), '--json', '--lang', 'my'], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['issues'], [])
        result = subprocess.run([sys.executable, str(ROOT / 'vpn_config_check.py'), str(ROOT / 'missing.json'), '--json'], capture_output=True)
        self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
