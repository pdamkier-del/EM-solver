# Blind unseen full

Offentlig kæde: parse → redigerbar Parsed → build → run_confirmed (separat proces) → Solution → Eksamen-rendering og LaTeX → uafhængige orakler. Autonomous bruger kun bankens opgavetekst; assisted-input er manuel transskription, ingen facitindsættelse.

| ID | Autonomous | Assisted | Method | Failure class | Kommentar |
|---|---|---|---|---|---|
| EV01 | PASS | PASS | gauss_radial | — |  |
| EV02 | FAIL | FAIL | composite | UNITS | Units not verified |
| EV03 | FAIL | PASS | gauss_radial | — |  |
| EV04 | PASS | PASS | gauss_radial | — |  |
| EV05 | FAIL | PASS | gauss_radial | — |  |
| EV06 | FAIL | PASS | gauss_radial | — |  |
| EV07 | FAIL | PASS | field_calculus | — |  |
| EV08 | FAIL | PASS | field_calculus | — |  |
| EV09 | FAIL | PASS | coulomb_integral | — |  |
| EV10 | FAIL | PASS | coulomb_integral | — |  |
| EV11 | FAIL | PASS | coulomb_integral | — |  |
| EV12 | FAIL | PASS | composite | — |  |
| EV13 | FAIL | FAIL | composite | SYMBOLIC_ALGEBRA |  |
| EV14 | FAIL | FAIL | composite | SYMBOLIC_ALGEBRA |  |
| EV15 | FAIL | FAIL | composite | SYMBOLIC_ALGEBRA |  |
| EV16 | FAIL | PASS | gauss_radial | — |  |
| EV17 | FAIL | PASS | composite | — |  |
| EV18 | FAIL | PASS | point_charges | — |  |
| EV19 | FAIL | PASS | laplace_legendre | — |  |
| BA01 | FAIL | PASS | ampere | — |  |
| BA02 | FAIL | PASS | ampere | — |  |
| BA03 | FAIL | PASS | ampere | — |  |
| BA04 | FAIL | PASS | composite | — |  |
| BA05 | FAIL | PASS | biot_savart | — |  |
| BA06 | FAIL | PASS | biot_savart | — |  |
| BA07 | FAIL | PASS | biot_savart | — |  |
| BA08 | FAIL | PASS | biot_savart | — |  |
| BA09 | FAIL | PASS | composite | — |  |
| BA10 | FAIL | PASS | field_calculus | — |  |
| BA11 | FAIL | PASS | field_calculus | — |  |
| BA12 | FAIL | PASS | composite | — |  |
| BA13 | FAIL | PASS | wire_force | — |  |
| BA14 | FAIL | FAIL | magnetic_dipole_interaction | METHOD_SELECTION | Ukendt kombination af område og metodefamilie. |
| BA15 | FAIL | PASS | magnetic_material | — |  |
| BA16 | FAIL | FAIL | composite | SYMBOLIC_ALGEBRA |  |
| DYN01 | FAIL | PASS | faraday | — |  |
| DYN02 | FAIL | PASS | dependency | — |  |
| DYN03 | FAIL | PASS | ampere_maxwell | — |  |
| DYN04 | FAIL | FAIL | inductance_energy | SYMBOLIC_ALGEBRA |  |
| DYN05 | FAIL | FAIL | resistance | METHOD_SELECTION | Tværsnitsareal skal være positiv; angiv positive symbolantagelser eller et positivt tal. |
| DYN06 | FAIL | PASS | dependency | — |  |
| DYN07 | FAIL | PASS | feedback | — |  |
| DYN08 | FAIL | PASS | motional_emf | — |  |
| DYN09 | FAIL | PASS | composite | — |  |
| DYN10 | FAIL | PASS | composite | — |  |
| DYN11 | FAIL | FAIL | composite | SYMBOLIC_ALGEBRA |  |
| DYN12 | FAIL | PASS | composite | — |  |
| DYN13 | FAIL | PASS | faraday | — |  |
| DYN14 | FAIL | PASS | motional_emf | — |  |
| DYN15 | FAIL | PASS | faraday | — |  |
| GEN01 | FAIL | PASS | coulomb_integral | — |  |
| GEN02 | FAIL | PASS | field_calculus | — |  |
| GEN03 | FAIL | PASS | field_calculus | — |  |
| GEN04 | PASS | PASS | None | — | Gauss-loven gælder, men en endelig cylinder har ikke tilstrækkelig symmetri til direkte bestemmelse af E ved et generelt punkt. Angiv fuld Coulomb-/potentialparameterisering. |
| GEN05 | FAIL | FAIL | None | PARSER | Ingen sikker beregningsvej. Angiv ladninger, rho/J og regioner, V/E/A eller B/flux med geometri. Parameteriserede linjer kræver source, parameter, bounds og point. |

## Metrics

```json
{
  "autonomous": {
    "total": 55,
    "passed": 3,
    "percent": 5.5,
    "correct_refusals": 1,
    "silent_wrong": 0,
    "timeouts": 0
  },
  "assisted": {
    "total": 55,
    "passed": 45,
    "percent": 81.8,
    "correct_refusals": 3,
    "silent_wrong": 4,
    "timeouts": 0
  },
  "domains": {
    "EV": {
      "autonomous": {
        "total": 19,
        "passed": 2,
        "percent": 10.5,
        "correct_refusals": 0,
        "silent_wrong": 0,
        "timeouts": 0
      },
      "assisted": {
        "total": 19,
        "passed": 15,
        "percent": 78.9,
        "correct_refusals": 0,
        "silent_wrong": 3,
        "timeouts": 0
      }
    },
    "BA": {
      "autonomous": {
        "total": 16,
        "passed": 0,
        "percent": 0.0,
        "correct_refusals": 0,
        "silent_wrong": 0,
        "timeouts": 0
      },
      "assisted": {
        "total": 16,
        "passed": 14,
        "percent": 87.5,
        "correct_refusals": 0,
        "silent_wrong": 0,
        "timeouts": 0
      }
    },
    "DYN": {
      "autonomous": {
        "total": 15,
        "passed": 0,
        "percent": 0.0,
        "correct_refusals": 0,
        "silent_wrong": 0,
        "timeouts": 0
      },
      "assisted": {
        "total": 15,
        "passed": 12,
        "percent": 80.0,
        "correct_refusals": 0,
        "silent_wrong": 1,
        "timeouts": 0
      }
    },
    "GEN": {
      "autonomous": {
        "total": 5,
        "passed": 1,
        "percent": 20.0,
        "correct_refusals": 1,
        "silent_wrong": 0,
        "timeouts": 0
      },
      "assisted": {
        "total": 5,
        "passed": 4,
        "percent": 80.0,
        "correct_refusals": 3,
        "silent_wrong": 0,
        "timeouts": 0
      }
    }
  },
  "failure_distribution": {
    "autonomous": {
      "INPUT_VALIDATION": 26,
      "UNITS": 2,
      "PARSER": 24
    },
    "assisted": {
      "UNITS": 1,
      "SYMBOLIC_ALGEBRA": 6,
      "METHOD_SELECTION": 2,
      "PARSER": 1
    }
  }
}
```

Baselinekode: reports/blind_baseline_source_manifest.json. Rå fortolkninger, resultater, warnings, checks og tider findes i rapportens JSON-sidefil. Testbanken er nu set; genkørsel efter fixes er regression på denne bank, ikke en ny blindtest.
