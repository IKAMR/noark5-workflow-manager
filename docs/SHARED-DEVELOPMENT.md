# Shared development: Noark 5 og SIARD Workflow Manager

Dette dokumentet beskriver hvordan generisk funksjonalitet skal holdes samordnet mellom:

- Noark 5 Workflow Manager: https://github.com/IKAMR/noark5-workflow-manager
- SIARD Workflow Manager: https://github.com/smult/SIARD-Workflow-Manager

Prosjektene skal kunne utvikles uavhengig. Vi deler derfor ikke én felles Python-pakke nå. I stedet skal generiske mønstre, grensesnitt og tester holdes bevisst sammenfallende der dette gir mening.

## Hovedregel

Når en ny funksjon foreslås eller implementeres, avgjør først om den er:

1. **generisk workflow/depot-funksjonalitet**, eller
2. **domene-spesifikk for Noark 5 eller SIARD**.

Generisk kode skal utformes uten unødvendige Noark- eller SIARD-antakelser. Domenespesifikk oppførsel skal ligge i kildemodeller, adaptere, operasjoner eller presentasjon.

Før endring av generisk funksjonalitet:

1. Kontroller `docs/SHARED-ROADMAP.md`.
2. Sjekk om søsterprosjektet allerede har en referanseimplementasjon.
3. Gjenbruk eller tilpass det etablerte generiske mønsteret når praktisk mulig.
4. Ikke kopier domenespesifikke antakelser mellom prosjektene.
5. Dokumenter bevisste forskjeller.

## Samarbeidsmodell

Generiske forbedringer kan utvikles først i en fork/branch der behovet oppstår. Etter praktisk test kan de:

- porteres til det andre Workflow Manager-prosjektet,
- sammenlignes med samme type tester,
- og foreslås tilbake til originalt prosjekt gjennom branch/PR når funksjonen er moden.

Dette gjør at Noark-arbeidet kan gå raskt uten å forstyrre SIARD Workflow Managers eget utviklingsløp.

## Referanseoversikt

| Område | Felles/generisk | Domenespesifikt | Nåværende referanse |
| --- | --- | --- | --- |
| Workflow/operasjonsmodell | Ja | operasjonene | Begge, holdes samordnet |
| Executor/backend-grense | Ja | kildeadgang | Noark 5 Workflow Manager |
| PREMIS-proveniens | Ja | objekt/formatering/detaljer | SIARD Workflow Manager, portert til Noark |
| DIAS metadata/pakkedialog | I stor grad | kildeinnhold | SIARD som utgangspunkt, Noark utvidet |
| Opprett mappe / legg til fil / legg til mappe | Ja | valgt pakkekontekst | Noark 5 Workflow Manager |
| Sist brukte mapper | Ja | konkrete felter | Noark 5 Workflow Manager |
| Transfer + verify + PREMIS | Ja | kildeobjekt/lagringsrolle | Planlagt |
| Rekursive batchjobber | Ja | discovery/prequalify-regler | Planlagt, tidligere Python-erfaring |
| Ekstern validator-integrasjon | Ja som mønster | Arkade/andre verktøy | Planlagt |
| Analysemodell | Delvis | Noark XML vs SIARD database | Domenespesifikk |
| AIP-finalisering/AIC-bygging | Ja som prosess | innholdsmodell | Planlagt |

## Når skal vi vurdere felles bibliotek?

Ikke ennå. Et eget shared GUI/core-repository kan være attraktivt, men vil koble release-løpene tett. Først når flere stabile komponenter faktisk er like i begge prosjektene og portering blir dyrere enn deling, bør et felles bibliotek vurderes.
