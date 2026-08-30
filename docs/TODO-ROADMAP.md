# ToDo og videre plan

Dette dokumentet samler konkrete åpne punkter og beslutninger som skal følges opp i videre utvikling.

## Operasjonssynlighet og modenhet

- Erstatt `0 / 1 / 2` i GUI med forståelige valg: `Alle (inkl. Alpha)`, `Beta og stabile`, `Kun stabile`.
- Modenhet defineres per operasjon som `alpha`, `beta` eller `stable`.
- Generell operasjonsmetadata ligger under `config/`, ikke under `noark5_workflow/`.
- `config/operations.json` er generell policyfil og kan justeres før commit.

## Jobber og identitet

- Dagens `JOB-001`-ID-er er midlertidige tekniske ID-er.
- Senere modell skal skille intern ID, kort label (f.eks. `1525_001`) og full label (f.eks. `1525_001 Velferd (1998-2018)`).
- Aktiv jobb skal være tydelig i hovedvindu og Jobber-vindu.
- Samme source kan brukes i flere jobber.
- Forskjellige jobber i samme jobbliste skal ikke bruke samme output-root.
- Eksisterende jobber skal kunne redigeres og kjøres på nytt uten tap av tidligere historikk.

## Workflow og kontrollpunkter

- Flere kontrollpunkter i samme workflow.
- Fortsett fra lagret execution cursor.
- Senere: kjør valgte operasjoner, retry, pause/resume og mer avansert scheduler.

## Resultater og AIC

- Innfør run-ID per kjøring og resultatregister per jobb.
- Innfør eksplisitt output-policy per operasjon.
- Skill arbeidsresultater/testhistorikk fra det som finaliseres til AIC.
- Gjør AIC-finalisering til eksplisitt workflow-steg med manifest/subset-valg.
- PREMIS og andre historikkfiler skal ikke overskrives stille ved rerun.

## Setup og kjøremiljø

- Setup eksport/import bruker plattformuavhengig JSON-format.
- Reset skal gi dokumenterte standardinnstillinger.
- På sikt flyttes runtime-state og brukerinnstillinger til plattformriktig per-user application-data-område.
- Test Windows RDS/Terminal Server før dette erklæres støttet.
- Senere Linux/macOS-launchere og testmatrise ved behov.

## Repositorystruktur

- Repo-root skal bare inneholde filer med klar root-rolle.
- Generell applogikk legges under `app/`.
- Generell konfigurasjon og policy legges under `config/`.
- `noark5_workflow/` skal bare brukes for Noark 5-spesifikk logikk.
- `settings.py` og `version.py` kan vurderes flyttet senere som en egen bevisst refaktorering, ikke midt i et funksjonelt fix-trinn.

## UI-konsistens

- Bruk knappereglene i `INTERFACE.md` konsekvent i nye dialoger.
- Gjennomgå resterende GUI ved senere UI-opprydding slik at primær, sekundær og stopp/fare har samme semantikk overalt.
