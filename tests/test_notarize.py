# SPDX-License-Identifier: AGPL-3.0-only
"""Distribution must never report success after a failed Apple submission."""
import importlib.util
import json
from pathlib import Path
import subprocess
from unittest.mock import Mock

import pytest

spec = importlib.util.spec_from_file_location('notarize', Path(__file__).resolve().parents[1] / 'scripts/notarize.py')
notarize = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notarize)


@pytest.mark.parametrize('metadata', [
    'Signature=adhoc\nTeamIdentifier=not set\n',
    'Authority=Apple Development: Example\nTeamIdentifier=TEST123456\nTimestamp=today\n',
    'Authority=Developer ID Application: Example (TEST123456)\nTeamIdentifier=TEST123456\n',
])
def test_untrusted_or_untimestamped_signature_rejected(metadata):
    with pytest.raises(ValueError):
        notarize.signature_team(metadata)


@pytest.mark.parametrize('status,code', [('Invalid', 0), ('In Progress', 1), ('Accepted', 1)])
def test_apple_rejection_or_timeout_does_not_staple_or_retry(tmp_path, monkeypatch, status, code):
    response = subprocess.CompletedProcess([], code, json.dumps({'id': 'test-id', 'status': status}), '')
    request = Mock(side_effect=[response, subprocess.CompletedProcess([], 0, '{}', '')])
    command = Mock()
    monkeypatch.setattr(notarize.subprocess, 'run', request)
    monkeypatch.setattr(notarize, 'run', command)
    with pytest.raises(RuntimeError, match='Apple did not accept'):
        notarize.submit(tmp_path / 'release.dmg', 'test-profile', tmp_path, 'dmg')
    assert request.call_count == 2  # One submission and its log; no resubmission.
    command.assert_not_called()
    assert json.loads((tmp_path / 'dmg-submission.json').read_text())['status'] == status


def test_non_json_response_is_not_success(tmp_path, monkeypatch):
    monkeypatch.setattr(notarize.subprocess, 'run', Mock(return_value=subprocess.CompletedProcess([], 1, '', 'network error')))
    command = Mock()
    monkeypatch.setattr(notarize, 'run', command)
    with pytest.raises(RuntimeError, match='no JSON result'):
        notarize.submit(tmp_path / 'app.zip', 'test-profile', tmp_path, 'app')
    command.assert_not_called()


def test_accepted_zip_staples_the_app_not_the_zip(tmp_path, monkeypatch):
    response = subprocess.CompletedProcess([], 0, json.dumps({'id': 'test-id', 'status': 'Accepted'}), '')
    monkeypatch.setattr(notarize.subprocess, 'run', Mock(side_effect=[response, subprocess.CompletedProcess([], 0, '{}', '')]))
    command = Mock()
    monkeypatch.setattr(notarize, 'run', command)
    app = tmp_path / 'Test.app'
    notarize.submit(tmp_path / 'app.zip', 'test-profile', tmp_path, 'app', staple_target=app)
    assert [call.args[0] for call in command.call_args_list] == [
        ['xcrun', 'stapler', 'staple', app], ['xcrun', 'stapler', 'validate', app]]


def test_missing_identity_never_starts_submission(tmp_path, monkeypatch):
    monkeypatch.setattr(notarize, 'run', Mock(return_value='0 valid identities found'))
    request = Mock()
    monkeypatch.setattr(notarize.subprocess, 'run', request)
    with pytest.raises(ValueError, match='No valid Developer ID'):
        notarize.notarize(tmp_path / 'Test.app', tmp_path / 'release.dmg',
            'Developer ID Application: Example (TEST123456)', 'test-profile', 'python3')
    request.assert_not_called()
    assert not (tmp_path / 'release.dmg').exists()
