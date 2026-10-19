"""Render Helm deployment scenarios and validate cross-resource invariants."""
import argparse
import pathlib
import shutil
import subprocess
import tarfile
import tempfile
import unittest

import yaml


parser = argparse.ArgumentParser()
parser.add_argument('--helm', default='helm')
args = parser.parse_args()
chart = pathlib.Path(__file__).resolve().parents[1] / 'charts' / 'memoharbor-legacy'


class HelmDeploymentTest(unittest.TestCase):
    def render(self, values=None, release='memo', namespace='helm-test', succeeds=True):
        with tempfile.TemporaryDirectory() as directory:
            overrides = pathlib.Path(directory) / 'values.yaml'
            overrides.write_text(yaml.safe_dump(values or {}), encoding='utf-8')
            result = subprocess.run(
                [args.helm, 'template', release, str(chart), '--namespace', namespace,
                 '--kube-version', '1.28.0', '-f', str(overrides)],
                capture_output=True, text=True, encoding='utf-8',
            )
        if not succeeds:
            self.assertNotEqual(0, result.returncode)
            self.assertIn('schema', result.stderr.lower())
            return
        self.assertEqual(0, result.returncode, result.stderr)
        return {item['kind']: item for item in yaml.safe_load_all(result.stdout) if item}

    def test_default_resources_share_selectors_and_external_configuration(self):
        resources = self.render()
        self.assertEqual({'Deployment', 'Service', 'ServiceAccount', 'Route'}, set(resources))
        for resource in resources.values():
            self.assertEqual('helm-test', resource['metadata']['namespace'])
        deployment = resources['Deployment']['spec']
        pod = deployment['template']['spec']
        container = pod['containers'][0]
        selector = deployment['selector']['matchLabels']
        self.assertEqual(selector, resources['Service']['spec']['selector'])
        self.assertEqual(selector, deployment['template']['metadata']['labels'])
        self.assertFalse(pod['automountServiceAccountToken'])
        self.assertTrue(pod['securityContext']['runAsNonRoot'])
        self.assertNotIn('runAsUser', pod['securityContext'])
        self.assertEqual('RuntimeDefault', pod['securityContext']['seccompProfile']['type'])
        self.assertFalse(container['securityContext']['allowPrivilegeEscalation'])
        self.assertEqual(['ALL'], container['securityContext']['capabilities']['drop'])
        self.assertEqual('memo', pod['serviceAccountName'])
        self.assertEqual('memoharbor-db', pod['volumes'][0]['secret']['secretName'])
        self.assertEqual(0o444, pod['volumes'][0]['secret']['defaultMode'])
        self.assertEqual([{'key': '.env', 'path': '.env'}], pod['volumes'][0]['secret']['items'])
        self.assertIn('-Dmemoharbor.env=/etc/memoharbor/.env', container['env'][0]['value'])
        self.assertEqual('/memoharbor/health', container['readinessProbe']['httpGet']['path'])
        self.assertEqual('/memoharbor/live', container['livenessProbe']['httpGet']['path'])
        self.assertEqual('memo', resources['Route']['spec']['to']['name'])
        self.assertEqual('Redirect', resources['Route']['spec']['tls']['insecureEdgeTerminationPolicy'])

    def test_overrides_use_digest_and_keep_all_names_and_ports_consistent(self):
        digest = 'sha256:' + 'a' * 64
        resources = self.render({
            'fullnameOverride': 'custom-memo', 'replicaCount': 3,
            'image': {'repository': 'registry.example.test/memo', 'digest': digest},
            'imagePullSecrets': [{'name': 'private-pull'}],
            'database': {'existingSecret': 'production-db', 'secretKey': 'config.env'},
            'service': {'port': 8181},
            'route': {'host': 'memo.example.test'},
            'podAnnotations': {'config-revision': '2'},
            'nodeSelector': {'kubernetes.io/arch': 'amd64'},
        })
        deployment = resources['Deployment']['spec']
        pod = deployment['template']['spec']
        self.assertEqual(3, deployment['replicas'])
        self.assertEqual('registry.example.test/memo@' + digest, pod['containers'][0]['image'])
        self.assertEqual([{'name': 'private-pull'}], pod['imagePullSecrets'])
        self.assertEqual('production-db', pod['volumes'][0]['secret']['secretName'])
        self.assertEqual('config.env', pod['volumes'][0]['secret']['items'][0]['key'])
        self.assertEqual('2', deployment['template']['metadata']['annotations']['config-revision'])
        self.assertEqual('amd64', pod['nodeSelector']['kubernetes.io/arch'])
        self.assertEqual('custom-memo', pod['serviceAccountName'])
        self.assertEqual('custom-memo', resources['Route']['spec']['to']['name'])
        self.assertEqual('memo.example.test', resources['Route']['spec']['host'])
        self.assertEqual(8181, resources['Service']['spec']['ports'][0]['port'])
        self.assertEqual(8080, pod['containers'][0]['ports'][0]['containerPort'])

    def test_route_and_service_account_can_be_external(self):
        resources = self.render({'route': {'enabled': False}, 'serviceAccount': {'create': False, 'name': 'existing'}})
        self.assertEqual({'Deployment', 'Service'}, set(resources))
        self.assertEqual('existing', resources['Deployment']['spec']['template']['spec']['serviceAccountName'])

    def test_releases_are_isolated_by_selector(self):
        first = self.render(release='first')
        second = self.render(release='second')
        self.assertNotEqual(first['Service']['spec']['selector'], second['Service']['spec']['selector'])
        self.assertNotEqual(first['Deployment']['metadata']['name'], second['Deployment']['metadata']['name'])

    def test_invalid_operational_values_fail_before_deployment(self):
        for values in [{'image': {'digest': 'sha256:bad'}}, {'replicaCount': -1},
                       {'database': {'existingSecret': ''}}, {'service': {'port': 65536}}]:
            with self.subTest(values=values):
                self.render(values, succeeds=False)

    def test_chart_package_excludes_environment_files(self):
        with tempfile.TemporaryDirectory() as directory:
            copy = pathlib.Path(directory) / chart.name
            shutil.copytree(chart, copy)
            (copy / '.env').write_text('excluded-test-marker', encoding='utf-8')
            (copy / '.env.production').write_text('excluded-test-marker', encoding='utf-8')
            subprocess.run([args.helm, 'package', str(copy), '--destination', directory],
                           check=True, capture_output=True)
            archive = next(pathlib.Path(directory).glob('*.tgz'))
            with tarfile.open(archive) as package:
                self.assertTrue(any(name.endswith('/Chart.yaml') for name in package.getnames()))
                self.assertFalse(any('/.env' in name for name in package.getnames()))


unittest.main(argv=['verify-helm'], verbosity=2)
