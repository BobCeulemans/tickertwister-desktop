# SPDX-License-Identifier: AGPL-3.0-only
"""The release archive must exclude working files and refuse unsafe links."""
import sys
import zipfile
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from source import package

def test_export_is_allowlisted(tmp_path):
    root = tmp_path / 'project'
    (root/'web').mkdir(parents=True)
    (root/'web'/'App.jsx').write_text('public source')
    (root/'web'/'__pycache__').mkdir()
    (root/'web'/'__pycache__'/'secret.pyc').write_text('cache')
    (root/'research.json').write_text('private research')
    (root/'.env').write_text('API key')
    (root/'.gitignore').write_text('.env')
    archive = tmp_path/'source.zip'
    package(root, archive)
    with zipfile.ZipFile(archive) as z:
        assert sorted(z.namelist()) == ['Tickertwister/.gitignore','Tickertwister/web/App.jsx']

def test_export_refuses_links_and_credentials(tmp_path):
    (tmp_path/'web').mkdir()
    outside = tmp_path/'private.txt'
    outside.write_text('private')
    link = tmp_path/'web'/'linked.txt'
    link.symlink_to(outside)
    with pytest.raises(ValueError, match='Symlink'):
        package(tmp_path, tmp_path/'source.zip')
    link.unlink()
    (tmp_path/'web'/'.env').write_text('key')
    with pytest.raises(ValueError, match='Private/build'):
        package(tmp_path, tmp_path/'source.zip')
