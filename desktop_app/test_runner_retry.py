"""Stub-based process test for backend runner retry; NOT a physics engine test."""
from pathlib import Path
import json, subprocess, sys, tempfile, shutil
original=Path(__file__).parent
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    for name in ('backend_runner.py','backend_paths.py','interpretation_aid.py'):
        shutil.copy2(original/name, root/name)
    vendor=root/'vendor'/'EM-solver'/'em1_solver';vendor.mkdir(parents=True)
    (vendor/'__init__.py').write_text('',encoding='utf8')
    (vendor/'backend_client.py').write_text('''
def run_text(text, corrections=None):
    if (corrections or {}).get('coordinate')=='s':
        return {'schema_version':'1.0','status':'verified_with_assumptions', 'interpretation':{},'solution':{'steps':[{'id':'a','latex':'Q=1'}]},'missing':[],'errors':[]}
    return {'schema_version':'1.0','status':'not_solved','interpretation':{},'solution':None,'missing':[],'errors':[]}
''',encoding='utf8')
    cases=[
      ('En cylinder, hvor s er den radiale afstand fra cylinderens akse.',{},0,True),
      ('En cylinder med E(s) og radius R.',{},2,False),
      ('En cylinder, hvor s er den radiale afstand.',{'coordinate':'r'},2,False),
    ]
    for i,(txt,corrections,code,auto) in enumerate(cases):
        task=root/f'task{i}.txt';result=root/f'reply{i}.json'
        task.write_text(txt,encoding='utf8')
        p=subprocess.run([sys.executable,str(root/'backend_runner.py'),'--input',str(task),
                          '--output',str(result),'--corrections',json.dumps(corrections)],capture_output=True,text=True)
        assert p.returncode==code,(txt,p.returncode,p.stderr)
        reply=json.loads(result.read_text(encoding='utf8'))
        assert ('desktop_text_corrections' in reply)==auto,(txt,reply)
        assert reply['desktop_user_corrections']==corrections
    print('3 procesbaserede retry-tests OK')
