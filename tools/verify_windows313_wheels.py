"""Inspect actual Windows wheels without claiming a native Windows installation."""
import sys,json,hashlib,zipfile,email,struct
from pathlib import Path
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.tags import cpython_tags,compatible_tags
from packaging.utils import parse_wheel_filename,canonicalize_name
from packaging.version import Version
ROOT=Path(__file__).resolve().parents[1]

def verify(folder):
    pins={canonicalize_name(r.name):str(r.specifier).removeprefix('==') for line in (ROOT/'desktop_app/requirements-windows-lock.txt').read_text().splitlines() if line.strip() and not line.startswith('#') for r in [Requirement(line)]}
    compatible=set(cpython_tags((3,13),platforms=['win_amd64']))|set(compatible_tags((3,13),interpreter='cp313',platforms=['win_amd64']))
    environment=dict(implementation_name='cpython',implementation_version='3.13.5',os_name='nt',platform_machine='AMD64',platform_python_implementation='CPython',platform_release='11',platform_system='Windows',platform_version='11',python_full_version='3.13.5',python_version='3.13',sys_platform='win32',extra='')
    rows={};dependencies={}
    for path in sorted(Path(folder).glob('*.whl')):
        name,version,_,tags=parse_wheel_filename(path.name);assert tags & compatible,path.name
        assert pins[name]==str(version),(name,version)
        pe_count=0
        with zipfile.ZipFile(path) as wheel:
            assert wheel.testzip() is None
            names=[n for n in wheel.namelist() if n.endswith('.dist-info/METADATA')];assert len(names)==1
            meta=email.message_from_bytes(wheel.read(names[0]));requires=meta.get('Requires-Python','')
            assert Version('3.13.5') in SpecifierSet(requires),(name,requires)
            dependencies[name]=meta.get_all('Requires-Dist',[])
            for member in wheel.namelist():
                if member.lower().endswith(('.pyd','.dll')):
                    raw=wheel.read(member)
                    assert raw[:2]==b'MZ',member
                    offset=struct.unpack_from('<I',raw,0x3c)[0];assert raw[offset:offset+4]==b'PE\0\0',member
                    machine=struct.unpack_from('<H',raw,offset+4)[0];assert machine==0x8664,(member,hex(machine));pe_count+=1
        rows[name]=dict(file=path.name,version=str(version),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),tags=sorted(str(t) for t in tags),requires_python=requires,amd64_pe_binaries=pe_count)
    assert set(rows)==set(pins),(set(rows)^set(pins))
    closure=[]
    for name,items in dependencies.items():
        for item in items:
            r=Requirement(item)
            if r.marker and not r.marker.evaluate(environment):continue
            dependency=canonicalize_name(r.name);assert dependency in rows,(name,item)
            assert Version(rows[dependency]['version']) in r.specifier,(name,item)
            closure.append(dict(package=name,requires=item,satisfied_by=rows[dependency]['version']))
    report=dict(target='standard CPython 3.13 x64, Windows',native_windows_tested=False,wheel_count=len(rows),all_wheels_crc_verified=True,requires_python_compatible=True,dependency_closure_satisfied=True,pe_architecture='AMD64 (0x8664)',packages=rows,dependencies=closure)
    target=ROOT/'reports/python313/windows_wheels.json';target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('packages','dependencies')}))

if __name__=='__main__':verify(sys.argv[1])
