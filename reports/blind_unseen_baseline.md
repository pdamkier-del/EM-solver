# Blind unseen baseline

Offentlig kæde: parse → redigerbar Parsed → build → run_confirmed (separat proces) → Solution → Eksamen-rendering og LaTeX → uafhængige orakler. Autonomous bruger kun bankens opgavetekst; assisted-input er manuel transskription, ingen facitindsættelse.

| ID | Autonomous | Assisted | Method | Failure class | Kommentar |
|---|---|---|---|---|---|
| EV01 | FAIL | PASS | gauss_radial | — |  |
| EV04 | FAIL | PASS | gauss_radial | — |  |
| EV05 | FAIL | PASS | gauss_radial | — |  |
| EV06 | FAIL | FAIL | gauss_radial | REGION_HANDLING | ('E', -8*a**3*rho0/(3*epsilon_0), -a**3*rho0/(3*epsilon_0)) |
| EV09 | FAIL | FAIL | coulomb_integral | UNITS | Units not verified |
| EV11 | FAIL | FAIL | coulomb_integral | UNITS | Units not verified |
| EV16 | FAIL | FAIL | gauss_radial | INPUT_VALIDATION | Denne beregningsvej bestemmer ikke P. Angiv en anden fysisk relation eller referencebetingelse. |
| EV19 | FAIL | FAIL | None | METHOD_SELECTION | Ingen sikker beregningsvej. Angiv ladninger, rho/J og regioner, V/E/A eller B/flux med geometri. Parameteriserede linjer kræver source, parameter, bounds og point. |
| BA01 | FAIL | PASS | ampere | — |  |
| BA02 | FAIL | PASS | ampere | — |  |
| BA05 | FAIL | FAIL | biot_savart | UNITS | Units not verified |
| BA10 | FAIL | PASS | field_calculus | — |  |
| BA15 | FAIL | FAIL | None | METHOD_SELECTION | Ingen sikker beregningsvej. Angiv ladninger, rho/J og regioner, V/E/A eller B/flux med geometri. Parameteriserede linjer kræver source, parameter, bounds og point. |
| DYN01 | FAIL | FAIL | None | METHOD_SELECTION | Ingen sikker beregningsvej. Angiv ladninger, rho/J og regioner, V/E/A eller B/flux med geometri. Parameteriserede linjer kræver source, parameter, bounds og point. |
| DYN02 | FAIL | PASS | dependency | — |  |
| DYN03 | FAIL | FAIL | None | METHOD_SELECTION | Ingen sikker beregningsvej. Angiv ladninger, rho/J og regioner, V/E/A eller B/flux med geometri. Parameteriserede linjer kræver source, parameter, bounds og point. |
| DYN07 | FAIL | FAIL | None | METHOD_SELECTION | Ingen sikker beregningsvej. Angiv ladninger, rho/J og regioner, V/E/A eller B/flux med geometri. Parameteriserede linjer kræver source, parameter, bounds og point. |
| DYN13 | FAIL | FAIL | None | METHOD_SELECTION | Ingen sikker beregningsvej. Angiv ladninger, rho/J og regioner, V/E/A eller B/flux med geometri. Parameteriserede linjer kræver source, parameter, bounds og point. |
| GEN02 | FAIL | PASS | field_calculus | — |  |
| GEN04 | FAIL | PASS | None | — | Uendelig cylinder er ikke bekræftet. Endelig kilde kræver fuld parameterisering til integral-fallback. |

## Metrics

```json
{
  "autonomous": {
    "total": 20,
    "passed": 0,
    "percent": 0.0,
    "correct_refusals": 0,
    "silent_wrong": 0,
    "timeouts": 0
  },
  "assisted": {
    "total": 20,
    "passed": 9,
    "percent": 45.0,
    "correct_refusals": 2,
    "silent_wrong": 0,
    "timeouts": 0
  },
  "domains": {
    "EV": {
      "autonomous": {
        "total": 8,
        "passed": 0,
        "percent": 0.0,
        "correct_refusals": 0,
        "silent_wrong": 0,
        "timeouts": 0
      },
      "assisted": {
        "total": 8,
        "passed": 3,
        "percent": 37.5,
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
        "passed": 3,
        "percent": 60.0,
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
        "passed": 1,
        "percent": 20.0,
        "correct_refusals": 0,
        "silent_wrong": 0,
        "timeouts": 0
      }
    },
    "GEN": {
      "autonomous": {
        "total": 2,
        "passed": 0,
        "percent": 0.0,
        "correct_refusals": 0,
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
      "PARSER": 19,
      "INPUT_VALIDATION": 1
    },
    "assisted": {
      "REGION_HANDLING": 1,
      "UNITS": 3,
      "INPUT_VALIDATION": 1,
      "METHOD_SELECTION": 6
    }
  }
}
```

Baselinekode: reports/blind_baseline_source_manifest.json. Rå fortolkninger, resultater, warnings, checks og tider findes i rapportens JSON-sidefil. Testbanken er nu set; genkørsel efter fixes er regression på denne bank, ikke en ny blindtest.
