# Jobs and batches

Introduced in v0.1.1. Job persistence, editing, checkpoints and controlled rerun are now part of the current development baseline.

## User-facing hierarchy

1. **Jobber** – oversikt over én eller flere jobber.
2. **Workflow** – detaljert arbeidsflate for én aktiv jobb.
3. **Resultater** – senere eget aggregert resultatnivå.

Scheduler og Worker er tekniske lag og skal normalt vises som status, ikke som egne hovedvinduer.

## Core model

```text
Jobbliste
├── JOB-001 -> source A -> workflow A -> output A
├── JOB-002 -> source B -> workflow B -> output B
└── JOB-003 -> source C -> workflow C -> output C
```

Én Job eier sin egen kilde, workflow, operasjonsparametre, utdata, status, execution cursor og kjørelogg.

## Persistente jobblister

Jobblister kan lagres og åpnes som `.n5jobs`.

Jobblista er brukerens eksplisitte, varige lagring. Store Noark 5-uttrekk bygges ikke inn i jobblistefila; kilde og output refereres med plassering.

Full crash-safe autosave/recovery av ulagrede endringer er ikke implementert ennå. Det er planlagt separat under app-workspace.

## Redigering og ny kjøring

Eksisterende jobber kan redigeres. Endring av workflow eller relevant operasjonskonfigurasjon skal invalidere gammel execution cursor når den ikke lenger er gyldig.

En tidligere ferdig eller feilet jobb kan kjøres på nytt etter eksplisitt bekreftelse. Ny kjøring skal ikke stille slette eller overskrive tidligere historikk.

## Kontrollpunkter og fortsettelse

En workflow kan ha `Stopp etter` på operasjoner.

Når et kontrollpunkt nås:

- jobben får status `Venter ved kontrollpunkt`
- neste operasjonsindeks lagres
- brukergrensesnittet tilbyr `Fortsett workflow`
- fortsettelse starter på neste operasjon i stedet for å kjøre ferdige operasjoner på nytt

Praktisk ende-til-ende-test av stopp, restart og fortsettelse krever minst to reelle operasjoner i samme workflow.

## Start alle

`Start alle` kjører jobbene sekvensielt på lokal worker.

- Hver jobb har egen status, fremdrift, melding og jobbspesifikk logg.
- Aktiv jobb skal være tydelig i hovedvindu og Jobber-vindu.
- Batch kan inneholde jobber som ender `Ferdig`, `Feil`, `Venter` eller `Hoppet over`.
- `Stopp` skal hindre at nye jobber startes etter at aktiv kjøring er avbrutt.
- Overordnet run-logg beskrives i `APP-WORKSPACE-AND-RUN-LOGS.md`.

## Per-jobb konfigurasjon og jobbisolasjon

Konfigurerbare operasjoner skal ha parametre lagret på Job-objektet. `operation_params` på jobbobjektet er autoritativ konfigurasjon for jobben.

Mutable operasjonsobjekter eller GUI-state skal ikke lekke parametre fra én jobb til en annen.

Samme source kan brukes av flere jobber.

Forskjellige jobber i samme jobbliste skal ikke bruke samme `output_root`.

## Output/resource locking

Det opprettes en `.noark5-workflow-manager.lock` i eksplisitt valgt utdataområde mens en jobb kjører. Dette hindrer samtidige skrivere mot samme utdataområde.

Ved normal avslutning fjernes låsen automatisk. Etter maskin-/prosesskrasj kan en lås bli liggende igjen; den skal ikke slettes automatisk uten kontroll fordi den kan representere en faktisk aktiv annen instans.

Locking erstatter ikke kravet om forskjellig `output_root` for forskjellige jobber.

## Historikk og resultater

PREMIS og andre historikkdata skal ikke overskrives stille ved rerun. Gjentatte kjøringer i samme jobbområde skal bevare relevant historikk.

Arbeidsresultater og testhistorikk er ikke det samme som innhold som senere finaliseres til AIC. Se `WORK-RESULTS-AND-AIC-FINALIZATION.md`.

## Planned execution layers

```text
Workflow -> Job -> Batch -> Scheduler -> Worker
```

Nåværende scheduler er lokal og sekvensiell. Parallellitet, prioritet, retry, pause/resume, persistent kø og remote workers kommer senere.

## Design rules

- Recursive discovery skal opprette/prekvalifisere Jobs, ikke kjøre direkte i GUI-loop.
- Store objekter skal ikke kopieres, pakkes ut eller hashes bare fordi de oppdages.
- Original/received sources er i utgangspunktet read-only.
- Hver jobb skal ha isolert output/proveniens.
- Remote/server execution skal bruke job specifications og storage references fremfor å sende store payloads gjennom GUI-et.
