# EM1 Solver – begrundelser som integreret solver-output

## Krav til Codex-backenden

Når den autonome solver leverer et resultat, skal den også levere en struktureret kæde af trin. For hvert trin:

- `title`: præcis handling, fx "Vælg Gauss-flade".
- `why`: fysikbaseret begrundelse baseret på **identificerede** symmetrier, materiale- og randbetingelser; forklar også hvorfor metoden giver en simplifikation.
- `math`: det/de LaTeX-udtryk, der faktisk er udledt af den symbolske motor; IKKE postulerede facitformler.
- `check`: enheds-, grænse-, fortegns-, randbetingelses- eller antagelseskontrol, hvis den kan foretages. Marker ellers hvad der mangler.

Derudover: status `verified`/`assumptions`/`partial`/`unsolved`, liste med eksplicitte antagelser og et selvstændigt `result`-felt.

### Eksempel på dataformat

```json
{
  "status": "verified",
  "method": "gauss_cylindrical",
  "assumptions": ["uendelig cylinder", "homogen volumenladning", "vakuum"],
  "steps": [
    {
      "title": "Vælg metode",
      "why": "Rotations- og translationssymmetri gør feltet radialt og konstant på en koaksial cylinders sideflade.",
      "math": "\\[\\mathbf{E}=E(s)\\hat{\\mathbf{s}}\\]",
      "check": "Forudsætter uendelig længde og homogen ladningstæthed"
    }
  ],
  "result": "\\[\\mathbf{E}(s)=...\\]"
}
```

`verified` i illustrationen er kun kontraktens mulige status, ikke en verifikation af eksempeldata.

**Vigtigt:** Forklaringerne skal genereres som del af løsningskæden og aldrig blot tilføjes efter løsningen som generisk prosa. Hvis solveren ikke kan dokumentere metodevalget, skal den rapportere usikkerhed eller afstå fra at svare. Tests skal tjekke både matematisk korrekthed og begrundelsernes faktiske gyldighed.
