"""Regression checks for version ordering, release validation and source overrides."""
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


updater = load('update-version')
release = load('prepare-release')
selector = load('select-rpm')
overrides = load('apply-system-library-overrides')


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.spec = Path(self.temp.name) / 'test.spec'
        self.output = Path(self.temp.name) / 'output'
        self.spec.write_text('''%global upstream_version 2.0.11.1
Name:           rpi-imager
Version:        2.0.11.1
Release:        3%{?dist}

%changelog
* Existing entry
''')
        self.original = self.spec.read_text()
        self.patch = patch.object(updater, 'SPEC', self.spec)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.env = patch.dict(os.environ, {'GITHUB_OUTPUT': str(self.output)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_unchanged_is_noop(self):
        self.assertFalse(updater.update_spec('2.0.11.1', 'Tester', False))
        self.assertEqual(self.spec.read_text(), self.original)

    def test_stable_update_resets_release_and_preserves_history(self):
        self.assertTrue(updater.update_spec('2.0.12', 'Tester', False))
        text = self.spec.read_text()
        self.assertIn('Version:        2.0.12\n', text)
        self.assertIn('Release:        1%{?dist}', text)
        self.assertIn('* Existing entry', text)
        self.assertIn('upstream_tag=v2.0.12', self.output.read_text())

    def test_manual_downgrade_rejected_without_mutation(self):
        with self.assertRaisesRegex(SystemExit, 'Refusing downgrade'):
            updater.update_spec('2.0.10', 'Tester', False)
        self.assertEqual(self.spec.read_text(), self.original)
        self.assertFalse(self.output.exists())

    def test_automatic_downgrade_is_noop(self):
        self.assertFalse(updater.update_spec('2.0.10', 'Tester', False, automatic=True))
        self.assertEqual(self.spec.read_text(), self.original)
        self.assertFalse(self.output.exists())

    def test_explicit_downgrade_allowed(self):
        self.assertTrue(updater.update_spec('2.0.10', 'Tester', False, allow_downgrade=True))

    def test_prerelease_transitions(self):
        for value in ('2.0.12-rc2', '2.0.12-rc10', '2.0.12'):
            self.assertTrue(updater.update_spec(value, 'Tester', '-' in value))
        with self.assertRaises(SystemExit):
            updater.update_spec('2.0.12-rc11', 'Tester', True)

    def test_validation_and_normalization(self):
        self.assertEqual(updater.normalize_upstream_version('v2.0.12-rc1'), '2.0.12-rc1')
        self.assertEqual(updater.rpm_version_from_upstream('2.0.12-rc1'), '2.0.12~rc1')
        for value in ('$(touch /tmp/bad)', '2.0\nmalicious', '2', '../2.0'):
            with self.assertRaises(SystemExit):
                updater.normalize_upstream_version(value)

    def test_latest_skips_drafts(self):
        with patch.object(updater, 'github_api_json', return_value=[
            {'draft': True, 'tag_name': 'v9.0'},
            {'tag_name': 'v2.0.12-rc1', 'prerelease': True},
        ]):
            self.assertEqual(updater.latest_release(True), ('2.0.12-rc1', True))


class ReleaseTests(unittest.TestCase):
    def test_tag_matches_upstream_and_packaging_release(self):
        release.validate_tag('rpm-v2.0.12-rc1-2', '2.0.12-rc1', '2')
        for tag in ('rpm-v2.0.12-rc1-1', 'rpm-v2.0.11-2', 'rpm-v2.0.12-rc1-2.fc44'):
            with self.assertRaises(SystemExit):
                release.validate_tag(tag, '2.0.12-rc1', '2')

    def test_selects_by_metadata_not_filename(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for name in ('main.rpm', 'debug.rpm', 'source.rpm'):
                (directory / name).touch()
            metadata = {'main.rpm': 'rpi-imager\tx86_64',
                        'debug.rpm': 'rpi-imager-debuginfo\tx86_64',
                        'source.rpm': 'rpi-imager\tsrc'}
            with patch.object(selector.subprocess, 'check_output',
                              side_effect=lambda cmd, **kw: metadata[Path(cmd[-1]).name]):
                self.assertEqual(selector.select_rpm(directory), directory / 'main.rpm')

    def test_missing_or_ambiguous_binary_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            with self.assertRaises(SystemExit):
                selector.select_rpm(directory)
            for name in ('first.rpm', 'second.rpm'):
                (directory / name).touch()
            with patch.object(selector.subprocess, 'check_output', return_value='rpi-imager\tx86_64'):
                with self.assertRaises(SystemExit):
                    selector.select_rpm(directory)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.previous = Path.cwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, self.previous)
        Path('rpi-imager.spec').write_text('%global upstream_version 2.0.12-rc1\n')
        Path('package.rpm').write_bytes(b'package fixture')
        self.output = Path('output').resolve()
        self.env = patch.dict(os.environ, {'GITHUB_OUTPUT': str(self.output)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.argv = patch.object(sys, 'argv', ['prepare-release.py', '--tag',
                                             'rpm-v2.0.12-rc1-2', '--rpm', 'package.rpm'])
        self.argv.start()
        self.addCleanup(self.argv.stop)
        self.package = 'rpi-imager-2.0.12~rc1-2.fc44'

    def test_release_body_uses_rpm_metadata_and_copies_binary(self):
        response = io.BytesIO(json.dumps({'tag_name': 'v2.0.12-rc1', 'prerelease': True}).encode())
        with patch.object(release, 'query', side_effect=['2', self.package, self.package, 'x86_64']), \
                patch.object(release.urllib.request, 'urlopen', return_value=response):
            release.main()
        self.assertEqual(Path('release/package.rpm').read_bytes(), b'package fixture')
        self.assertIn(self.package + '.x86_64', Path('release/notes.md').read_text())
        self.assertIn('prerelease=true', self.output.read_text())

    def test_mismatched_binary_fails_before_api_or_publication(self):
        with patch.object(release, 'query', side_effect=['2', self.package, 'rpi-imager-2.0.10-1.fc44']), \
                patch.object(release.urllib.request, 'urlopen') as api:
            with self.assertRaisesRegex(SystemExit, 'does not match spec'):
                release.main()
            api.assert_not_called()
        self.assertFalse(Path('release').exists())

    def test_incorrect_upstream_metadata_fails(self):
        response = io.BytesIO(json.dumps({'tag_name': 'v2.0.10'}).encode())
        with patch.object(release, 'query', side_effect=['2', self.package, self.package, 'x86_64']), \
                patch.object(release.urllib.request, 'urlopen', return_value=response):
            with self.assertRaisesRegex(SystemExit, 'does not match'):
                release.main()
        self.assertFalse(Path('release').exists())


class OverrideTests(unittest.TestCase):
    def test_overrides_are_idempotent_and_reject_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for relative, (marker, block) in overrides.INSERTIONS.items():
                with self.subTest(path=relative):
                    target = root / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(marker + 'original body\n')
                    self.assertTrue(overrides.apply_override(root, relative, marker, block))
                    updated = target.read_text()
                    self.assertFalse(overrides.apply_override(root, relative, marker, block))
                    self.assertEqual(target.read_text(), updated)
                    target.write_text('changed upstream marker\n')
                    with self.assertRaises(RuntimeError):
                        overrides.apply_override(root, relative, marker, block)


if __name__ == '__main__':
    unittest.main()
