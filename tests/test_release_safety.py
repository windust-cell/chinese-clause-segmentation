import importlib.util
from pathlib import Path
import pytest
import hashlib
import io
import stat
import tarfile
import zipfile

spec = importlib.util.spec_from_file_location('release_audit', Path(__file__).parents[1]/'scripts'/'audit_release.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

@pytest.mark.parametrize('name', ['../outside', '/absolute', 'C'+':/outside', 'a/../../outside', r'a\..\outside', 'a/data.csv', 'a/.env'])
def test_unsafe_member_rejected(name):
    with pytest.raises(SystemExit):
        audit.check_member(name)

@pytest.mark.parametrize('options', [{'link': True}, {'special': True}])
def test_link_or_special_rejected(options):
    with pytest.raises(SystemExit):
        audit.check_member('package/item', **options)

def test_regular_members_allowed():
    for name in ['package/src/core.py', 'package/evaluation/results.json', 'package/LICENSE']:
        audit.check_member(name)

def test_scanner_cannot_hide_secret_in_its_own_file():
    with pytest.raises(SystemExit):
        audit.inspect('scripts/audit_release.py', ('gh'+'p_'+'A'*30).encode())

@pytest.mark.parametrize('kind', ['traversal', 'symlink', 'special', 'sensitive', 'case_collision'])
def test_real_zip_rejected_read_only(tmp_path, kind):
    path = tmp_path/'candidate.zip'
    with zipfile.ZipFile(path, 'w') as bundle:
        name = '../outside' if kind == 'traversal' else 'package/item'
        if kind == 'sensitive':
            name = 'package/data.sqlite'
        info = zipfile.ZipInfo(name)
        if kind == 'symlink':
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
        if kind == 'special':
            info.external_attr = stat.S_IFIFO << 16
        bundle.writestr(info, 'benign')
        if kind == 'case_collision':
            bundle.writestr('PACKAGE/ITEM', 'benign')
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(SystemExit):
        audit.audit_archive(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert not (tmp_path/'outside').exists()

@pytest.mark.parametrize('kind', [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE])
def test_real_tar_links_and_special_rejected(tmp_path, kind):
    path = tmp_path/'candidate.tar.gz'
    with tarfile.open(path, 'w:gz') as bundle:
        info = tarfile.TarInfo('package/item')
        info.type = kind
        info.linkname = 'other'
        bundle.addfile(info)
    with pytest.raises(SystemExit):
        audit.audit_archive(path)

def test_normal_development_content_and_archive(tmp_path):
    payload = b'{"token": "ordinary_word", "password": "example"}'
    audit.inspect('evaluation/results.json', payload)
    path = tmp_path/'candidate.zip'
    with zipfile.ZipFile(path, 'w') as bundle:
        bundle.writestr('evaluation/results.json', payload)
    audit.audit_archive(path)

def test_resource_limit(tmp_path):
    path = tmp_path/'candidate.tar'
    with tarfile.open(path, 'w') as bundle:
        info = tarfile.TarInfo('package/oversized')
        info.size = 17*1024*1024
        bundle.addfile(info, io.BytesIO(b'x'*info.size))
    with pytest.raises(SystemExit, match='resource limits'):
        audit.audit_archive(path)
