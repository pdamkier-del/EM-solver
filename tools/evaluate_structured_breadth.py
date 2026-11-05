"""Eight-group known-exam replay: solve without expected, then check cached answers.

This measures existing typed paths, not a parser, independent blind set or a
questionnaire's ability to elicit a correct physical model from a student.
"""
import copy
import json
import sys
from collections import Counter
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from em1_solver.core.historical import paths,load,run
from em1_solver.core.task_runtime import block_network

GROUPS={
    'coulomb_superposition':{'point_charges','coulomb_integral'},
    'gauss_nonuniform':{'gauss_radial'},
    'potential_energy_multipoles':{'field_calculus','potential_from_field','multipole'},
    'laplace_poisson':{'laplace_legendre'},
    'conductors_dielectrics_boundaries':{'conductors','capacitance','polarization','images'},
    'biot_savart_ampere':{'ampere','biot_savart','magnetic_superposition','wire_force','lorentz_force'},
    'magnetization_bound_currents':{'magnetic_material'},
    'induction_circuits':{'faraday','motional_emf','circuit_power','feedback','resistance','inductance_energy','ampere_maxwell','rc_transient'},
}


def main():
    block_network();records=[]
    for path in paths():
        recipe=load(path)
        families={s['problem']['family'] for s in recipe.get('path',[])}
        groups=[name for name,group in GROUPS.items() if families & group]
        row=dict(id=recipe['id'],groups=groups,outcome='reasoned_refusal',first_failure=None)
        if recipe['status'] not in ('executable','partial'):
            row['first_failure']='historical_model_not_executable';records.append(row);continue
        try:
            runtime=copy.deepcopy(recipe);runtime['expected']=[]
            answers=run(runtime).solutions
            # Comparison replays only cached results; no reference is passed to
            # a physics solver. Existing evaluator performs sign/unit/numeric checks.
            cached=iter(answers.values())
            with patch('em1_solver.core.registry.solve',side_effect=lambda p:next(cached)):
                compared=run(recipe)
            row.update(outcome=('partial' if recipe['status']=='partial' else 'correct_assisted') if compared.passed else 'incorrect',checks=compared.checks)
            if not compared.passed:row['first_failure']='official_reference_comparison'
        except Exception as exc:row.update(outcome='incorrect',first_failure='typed_execution_or_reference_check',error=str(exc))
        records.append(row)
    keys=['correct_autonomous','correct_assisted','partial','reasoned_refusal','incorrect']
    summary={key:sum(r['outcome']==key for r in records) for key in keys}
    grouped={g:{key:sum(r['outcome']==key for r in records if g in r['groups']) for key in keys} for g in GROUPS}
    report=dict(limitation='Previously known expert-encoded historical paths. Groups overlap. Not raw-text autonomy, independent blind generalization or end-user desktop validation.',summary=summary,groups=grouped,records=records)
    out=ROOT/'reports/assisted_evening';out.mkdir(parents=True,exist_ok=True)
    (out/'structured_breadth.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(summary=summary,groups=grouped)))


if __name__=='__main__':main()
