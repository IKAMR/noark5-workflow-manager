# Jobs and batches

Introduced in v0.1.1. Job persistence, editing, checkpoints and controlled rerun are now part of the current development baseline.

## User-facing hierarchy

1. **Jobber** – oversikt over én eller flere jobber.
2. **Workflow** – detaljert arbeidsflate for én aktiv jobb.
3. **Resultater** – senere eget aggregert resultatnivå.

Scheduler og Worker er tekniske lag og skal normalt vises som status, ikke som egne hovedvinduer.

Denne hierarkien beskriver GUI-flaten, men Job/Jobbliste/Workflow-modellen er ikke avhengig av desktop-GUI-et. Fra v0.1.2-a7 bruker lokal CLI de samme jobbobjektene og samme executor-/workflowsemantikk for kontroll og kjøring av eksisterende jobblister. Senere API skal bygge videre på samme modell.

## Core model

```text
Jobbliste
├── JOB-001 -> source A -> workflow A -> output A
├── JOB-002 -> source B -> workflow B -> output B
└── JOB-003 -> source C -> workflow C -> output C
```

Én Job eier sin egen kilde, workflow, operasjonsparametre, utdata, status, execution cursor og kjørelogg.

Jobbtilstand skal eies av jobb-/workflowmodellen, ikke av GUI-state alene.

## Persistente jobblister

Jobblister kan lagres og åpnes som `.n5jobs`.

Jobblista er brukerens eksplisitte, varige lagring. Store Noark 5-uttrekk bygges ikke inn i jobblistefila; kilde og output refereres med plassering.

Full crash-safe autosave/recovery av ulagrede endringer er ikke implementert ennå. Det er planlagt separat under app-workspace.

`.n5jobs` er også den implementerte inngangen for CLI-basert kontroll og batchkjøring i v0.1.2-a7. Filformatet er ikke GUI-spesifikt.

## Redigering og ny kjøring

Eksisterende jobber kan redigeres. Endring av workflow eller relevant operasjonskonfigurasjon skal invalidere gammel execution cursor når den ikke lenger er gyldig.

En tidligere ferdig eller feilet jobb kan kjøres på nytt etter eksplisitt bekreftelse. Ny kjøring skal ikke stille slette eller overskrive tidligere historikk.

GUI bruker brukerbekreftelse. CLI-et bruker eksplisitt `--rerun` for jobblister som inneholder terminale jobber. Samme sikkerhetsprinsipp skal bevares ved senere API-styring. Se `CLI.md` for gjeldende CLI-kontrakt.

## Kontrollpunkter og fortsettelse

En workflow kan ha kontrollpunkt etter operasjoner. I workflow-raden vises et aktivt kontrollpunkt med det fylte stoppsymbolet `■`; ingen symbol betyr at workflowen går direkte videre.

Når et kontrollpunkt nås:

- jobben får status `Venter ved kontrollpunkt`
- neste operasjonsindeks lagres
- brukergrensesnittet tilbyr `Fortsett workflow`
- fortsettelse starter på neste operasjon i stedet for å kjøre ferdige operasjoner på nytt

Praktisk ende-til-ende-test av stopp, restart og fortsettelse krever minst to reelle operasjoner i samme workflow.

Den underliggende `JobRunner` støtter execution cursor/checkpoint-semantikken uten GUI-avhengighet. Fra v0.1.2-a11 er fortsettelse også en eksplisitt delt Core-kontrakt gjennom `JobRunner.continue_job()`. Den validerer ventestatus, execution cursor og at ventetilstanden faktisk følger et kontrollpunkt, og gjenbruker deretter ordinær `JobRunner.run()` fra neste operasjon.

CLI eksponerer dette som:

```text
n5wf jobs continue <file.n5jobs> --job <job-id>
```

GUI-et bruker den samme `continue_job()`-kontrakten når aktiv jobb står `Venter ved kontrollpunkt`. Dermed har GUI og CLI samme styringssemantikk for fortsettelse.

## Start alle og BatchRunner

`Start alle` kjører jobbene sekvensielt på lokal worker. Den samme underliggende batchsemantikken ligger fra v0.1.2-a5 i GUI-uavhengig `BatchRunner`, som også brukes av CLI-et i a7.

- Hver jobb har egen status, fremdrift, melding og jobbspesifikk logg.
- Aktiv jobb skal være tydelig i hovedvindu og Jobber-vindu.
- Batch kan inneholde jobber som ender `Ferdig`, `Feil`, `Venter` eller `Hoppet over`.
- `Stopp` i GUI skal hindre at nye jobber startes etter at aktiv kjøring er avbrutt.
- Overordnet run-logg beskrives i `APP-WORKSPACE-AND-RUN-LOGS.md`.
- CLI kan kontrollere, kjøre og fortsette eksisterende `.n5jobs` med `n5wf jobs check`, `n5wf jobs run` og `n5wf jobs continue`.

## Preflight

`JobPreflight` er GUI-uavhengig og brukes til sikre kontroller/normaliseringer før kjøring. Dette omfatter blant annet stale `RUNNING`, execution cursor, output-konflikter og identifisering av jobber som krever eksplisitt rerun-beslutning.

GUI bestemmer hvordan brukeren spørres. CLI representerer den samme beslutningen maskinrettet, blant annet gjennom `--rerun`.

## Per-jobb konfigurasjon og jobbisolasjon

Konfigurerbare operasjoner skal ha parametre lagret på Job-objektet. `operation_params` på jobbobjektet er autoritativ konfigurasjon for jobben.

Mutable operasjonsobjekter eller GUI-state skal ikke lekke parametre fra én jobb til en annen.

Samme source kan brukes av flere jobber.

Forskjellige jobber i samme jobbliste skal ikke bruke samme `output_root`.

## Output/resource locking

Det opprettes en `.noark5-workflow-manager.lock` i eksplisitt valgt utdataområde mens en jobb kjører. Dette hindrer samtidige skrivere mot samme utdataområde.

Ved normal avslutning fjernes låsen automatisk. Etter maskin-/prosesskrasj kan en lås bli liggende igjen; den skal ikke slettes automatisk uten kontroll fordi den kan representere en faktisk aktiv annen instans.

Locking erstatter ikke kravet om forskjellig `output_root` for forskjellige jobber.

Locking-reglene gjelder uavhengig av om jobben startes fra GUI eller CLI, og skal også gjelde ved senere remote/server-grensesnitt.

## Historikk og resultater

PREMIS og andre historikkdata skal ikke overskrives stille ved rerun. Gjentatte kjøringer i samme jobbområde skal bevare relevant historikk.

Arbeidsresultater og testhistorikk er ikke det samme som innhold som senere finaliseres til AIC. Se `WORK-RESULTS-AND-AIC-FINALIZATION.md`.

## Execution layers

```text
Workflow -> Job -> Batch -> Scheduler -> Worker
```

Nåværende scheduler er lokal og sekvensiell. Parallellitet, prioritet, retry, pause/resume, persistent kø og remote workers kommer senere.

Klient-/styringslaget ligger konseptuelt foran denne kjeden:

```text
GUI / CLI / framtidig API
          |
          v
  JobPreflight / JobRunner / BatchRunner
          |
          v
   Job / Workflow layer
          |
          v
Workflow -> Job -> Batch -> Scheduler -> Worker
```

## Design rules

- Recursive discovery skal opprette/prekvalifisere Jobs, ikke kjøre direkte i GUI-loop.
- Store objekter skal ikke kopieres, pakkes ut eller hashes bare fordi de oppdages.
- Original/received sources er i utgangspunktet read-only.
- Hver jobb skal ha isolert output/proveniens.
- Remote/server execution skal bruke job specifications og storage references fremfor å sende store payloads gjennom GUI-et.
- Jobb- og workflowfunksjoner som skal være tilgjengelige fra flere grensesnitt skal ikke implementeres bare i GUI- eller CLI-handlere.
