# Blind unseen after

Offentlig kæde: parse → redigerbar Parsed → build → run_confirmed (separat proces) → Solution → Eksamen-rendering og LaTeX → uafhængige orakler. Autonomous bruger kun bankens opgavetekst; assisted-input er manuel transskription, ingen facitindsættelse.

| ID | Autonomous | Assisted | Method | Failure class | Kommentar |
|---|---|---|---|---|---|
| EV01 | PASS | PASS | gauss_radial | — |  |
| EV04 | PASS | PASS | gauss_radial | — |  |
| EV05 | FAIL | PASS | gauss_radial | — |  |
| EV06 | FAIL | PASS | gauss_radial | — |  |
| EV09 | FAIL | PASS | coulomb_integral | — |  |
| EV11 | FAIL | PASS | coulomb_integral | — |  |
| EV16 | FAIL | PASS | gauss_radial | — |  |
| EV19 | FAIL | PASS | laplace_legendre | — |  |
| BA01 | FAIL | PASS | ampere | — |  |
| BA02 | FAIL | PASS | ampere | — |  |
| BA05 | FAIL | PASS | biot_savart | — |  |
| BA10 | FAIL | PASS | field_calculus | — |  |
| BA15 | FAIL | PASS | magnetic_material | — |  |
| DYN01 | FAIL | PASS | faraday | — |  |
| DYN02 | FAIL | PASS | dependency | — |  |
| DYN03 | FAIL | PASS | ampere_maxwell | — |  |
| DYN07 | FAIL | PASS | feedback | — |  |
| DYN13 | FAIL | PASS | faraday | — |  |
| GEN02 | FAIL | PASS | field_calculus | — |  |
| GEN04 | PASS | PASS | None | — | Gauss-loven gælder, men en endelig cylinder har ikke tilstrækkelig symmetri til direkte bestemmelse af E ved et generelt punkt. Angiv fuld Coulomb-/potentialparameterisering. |

## Metrics

```json
{
  "autonomous": {
    "total": 20,
    "passed": 3,
    "percent": 15.0,
    "correct_refusals": 1,
    "silent_wrong": 0,
    "timeouts": 0
  },
  "assisted": {
    "total": 20,
    "passed": 20,
    "percent": 100.0,
    "correct_refusals": 2,
    "silent_wrong": 0,
    "timeouts": 0
  },
  "domains": {
    "EV": {
      "autonomous": {
        "total": 8,
        "passed": 2,
        "percent": 25.0,
        "correct_refusals": 0,
        "silent_wrong": 0,
        "timeouts": 0
      },
      "assisted": {
        "total": 8,
        "passed": 8,
        "percent": 100.0,
        "correct_refusals": 0,
        "silent_wrong": 0,
        "timeouts": 0
      }
    },
    "BA": {
      "autonomous": {
        "total": 5,
        "passed": 0,
        "percent": 0.0,
        "correct_refusals": 0,
        "silent_wrong": 0,
        "timeouts": 0
      },
      "assisted": {
        "total": 5,
        "passed": 5,
        "percent": 100.0,
        "correct_refusals": 0,
        "silent_wrong": 0,
        "timeouts": 0
      }
    },
    "DYN": {
      "autonomous": {
        "total": 5,
        "passed": 0,
        "percent": 0.0,
        "correct_refusals": 0,
        "silent_wrong": 0,
        "timeouts": 0
      },
      "assisted": {
        "total": 5,
        "passed": 5,
        "percent": 100.0,
        "correct_refusals": 0,
        "silent_wrong": 0,
        "timeouts": 0
      }
    },
    "GEN": {
      "autonomous": {
        "total": 2,
        "passed": 1,
        "percent": 50.0,
        "correct_refusals": 1,
        "silent_wrong": 0,
        "timeouts": 0
      },
      "assisted": {
        "total": 2,
        "passed": 2,
        "percent": 100.0,
        "correct_refusals": 2,
        "silent_wrong": 0,
        "timeouts": 0
      }
    }
  },
  "failure_distribution": {
    "autonomous": {
      "PARSER": 16,
      "INPUT_VALIDATION": 1
    },
    "assisted": {}
  }
}
```

Baselinekode: reports/blind_baseline_source_manifest.json. Rå fortolkninger, resultater, warnings, checks og tider findes i rapportens JSON-sidefil. Testbanken er nu set; genkørsel efter fixes er regression på denne bank, ikke en ny blindtest.

## Sammenligning med baseline

| Metric | Baseline | Efter fixes |
|---|---:|---:|
| Autonomous | 0/20 (0.0 %) | 3/20 (15.0 %) |
| Assisted | 9/20 (45.0 %) | 20/20 (100.0 %) |
| Silent wrong (assisted) | 0 | 0 |
| Timeout (assisted) | 0 | 0 |

Måleforbehold og rettelser: [blind_unseen_summary.md](blind_unseen_summary.md).
