# Code map og samspill mellom kilder

Målet med dette dokumentet er at en utvikler eller AI raskt skal finne riktig lag uten å lese hele kodebasen først.

## Nåværende hovedflyt

```text
Desktop GUI -------------------+
                               |
CLI: noark5_workflow/cli.py ---+
                               |
                               v
                     JobPreflight
              noark5_workflow/core/preflight.py
                               |
                               v
                      BatchRunner / JobRunner
       noark5_workflow/core/batch_runner.py
         noark5_workflow/core/job_runner.py
                               |
                               v
                     Executor boundary
              noark5_workflow/executors/
                               |
                               v
                         Operation
              noark5_workflow/operations/
                               |
                               +--> Noark source model
                               |    noark5_workflow/sources/
                               |
                               +--> output/report/package
                               |
                               +--> central PREMIS logger
                                    noark5_workflow/core/premis_logger.py
```

GUI og CLI skal ikke implementere analyse eller pakking direkte. Operasjoner skal ikke omgå executorlaget når de kjøres gjennom workflow.

## Flergrensesnitt-flyt

GUI og CLI er nå konkrete innganger. Senere API-/servergrensesnitt skal bruke samme underliggende jobb-/workflow-/executorlag.

```text
Desktop GUI --------+
CLI ----------------+--> Preflight / BatchRunner / JobRunner --> Workflow / Job --> Executor --> Operation
framtidig API ------+
```

`JobPreflight`, `BatchRunner` og `JobRunner` er den implementerte delte kjøregrensen for lokal jobb-/batchkjøring. Jobb-, jobbliste- og workflowfunksjoner som skal være tilgjengelige fra flere klienter skal ikke implementeres bare i GUI- eller CLI-handlere.

Den offentlige `n5wf`-kommandomodellen dokumenteres i `CLI.md`.

## Viktige moduler

### `noark5_workflow/cli.py`

CLI-adapteren. Leser kommandoer/argumenter, laster `.n5jobs`, bruker `JobPreflight`, `BatchRunner`, `JobRunner` og `LocalExecutor`, skriver terminalstatus og returnerer definerte exit codes. Skal ikke utvikles til en separat workflow-motor.

### `noark5_workflow/core/preflight.py`

GUI-uavhengig preflight for jobb-/batchkjøring. Håndterer sikre normaliseringer og rapporterer blant annet output-konflikter og behov for eksplisitt rerun-beslutning.

### `noark5_workflow/core/job_runner.py`

GUI-uavhengig kjøring av én `Job` gjennom executorlaget, inkludert execution cursor, checkpoints, output lock og status/resultat.

### `noark5_workflow/core/batch_runner.py`

GUI-uavhengig sekvensiell kjøring av en samling jobber ved å gjenbruke `JobRunner`.

### `noark5_workflow/core/context.py`

Felles kontekst for en workflow-kjøring. Skal etter hvert bære strukturerte resultater, lagringsroller og referanser som flere operasjoner kan gjenbruke.

### `noark5_workflow/core/operation.py`

Kontrakten for operasjoner. PREMIS-egenskaper skal deklareres her/av operasjonen; XML-skriving skal ikke ligge i domenefunksjonen.

### `noark5_workflow/core/premis_logger.py`

Sentral workflow-PREMIS, portert/adapted fra SIARD Workflow Manager. Denne skal være eneste standardmekanisme for workflow-PREMIS.

### `noark5_workflow/executors/`

Kjøregrense. `LocalExecutor` brukes nå. Fremtidig `RemoteExecutor` skal bevare samme operasjonskontrakt.

### `noark5_workflow/operations/dias_package.py`

DIAS/AIC-relatert pakking. Pakkenivået skal ikke endre kildeuttrekket. Fil/mappe-tillegg til package tree er et pakkevalg, ikke kildeendring.

## Planlagt analyseflyt

```text
Noark extraction
   |
   +--> arkivstruktur.xml
   +--> øvrige Noark XML
   +--> dokumenter/
            |
            v
   streamed/shared analysis model
            |
     +------+------+------+
     |      |      |      |
     v      v      v      v
   U1     U2     QA   reports
```

Store kilder skal ikke reparses for hver rapport når samme strukturdata kan gjenbrukes.

TAR-baserte Noark 5-kilder bør i tillegg kunne leses selektivt/strømmet uten full uttrekking når analysen tillater det. Dette endrer ikke den logiske analysemodellen over.

## Planlagt ekstern validatorflyt

```text
Operation
   |
   v
External tool adapter
   |
   +--> Arkade 5 CLI
   |
   v
capture exit/log/reports
   |
   v
normalized OperationResult
   |
   +--> workflow log
   +--> harvested analysis
   +--> relevant PREMIS event
```

Arkade 5 skal behandles som en uavhengig validator. Våre Python-kontroller skal kunne sammenlignes med resultatene, ikke skjules bak Arkade.

## Planlagt transfer/zone-flyt

```text
ORIGINAL_RECEIVED
       |
       | Transfer + SHA-256 verify + PREMIS
       v
QUARANTINE
       |
       | Transfer + verify + PREMIS
       v
WORKING
       |
       | validation / debug / reports
       v
FINAL_AIP
       |
       | explicit curated finalization
       v
AIC_OUTPUT
       |
       | final verification / transfer
       v
PRESERVATION_STORAGE
```

Kilde og destinasjon skal alltid være eksplisitte. Når bruker har valgt output, skal generert materiale ikke falle tilbake til kildens mappe.

## Batch og framtidig recursive-flyt

Den sekvensielle kjernen for en eksisterende jobbliste er implementert i `BatchRunner` og kan startes fra både GUI og CLI. Recursive discovery av nye kandidater er fortsatt planlagt.

```text
Recursive controller (planlagt)
   |
   +--> discover candidates
   +--> prequalify each candidate
   +--> construct normal Job / workflow
   |
   v
BatchRunner
   |
   v
JobRunner -> Executor -> Operations
```

Batchlaget skal orkestrere eksisterende operasjoner, ikke ha egne skjulte kopier av validator-/rapportkode.

## SIARD-kode som referanse

Før nye generiske komponenter lages, sjekk SIARD Workflow Manager. PREMIS er et konkret eksempel der SIARD eier referansemønsteret og Noark tilpasser objekt-/domeneinformasjon. Se `SHARED-DEVELOPMENT.md` for eierskap og portering.
