# App-arbeidsområde og overordnet kjørelogg

## Formål

`temp_dir` er rot for Noark 5 Workflow Managers lokale arbeidsområde. Arbeidsområdet kan inneholde flere interne undermapper og skal ikke behandles som én flat temp-katalog.

## Standardstruktur

Når egne mapper ikke er konfigurert, brukes:

```text
<temp_dir>/
    logs/
        runs/
    setup/
    joblists/
    work/
    cache/
```

`work/` og `cache/` er reserverte interne områder for senere bruk.

## Konfigurerbare standardmapper

Tre områder kan overstyres i innstillinger:

- `run_log_dir`
- `setup_dir`
- `job_list_dir`

Tom verdi betyr fallback til standard undermappe under `temp_dir`.

Dette er forskjellig fra `last_setup_dir` og `last_job_list_dir`, som bare beskriver hvor brukeren sist åpnet/lagret noe.

## Overordnet kjørelogg

Det opprettes én menneskelesbar `.log`-fil per kjøring:

- enkeltkjøring: én jobbseksjon
- batchkjøring: samme format, med én jobbseksjon per jobb

Loggen inneholder overordnet informasjon, ikke detaljene som allerede finnes i den enkelte jobb/output:

- run-ID
- single/batch
- app-versjon
- start/slutt
- jobbliste hvis relevant
- utførende brukers `username`, `user_id`, navn og e-post
- jobb-ID og navn
- jobbeiers `username`, `user_id`, navn og e-post
- source
- output
- jobbens start/slutt
- status og kort resultat
- totalsammendrag

**Utførende bruker** er snapshot av aktiv registrert bruker når run-loggen opprettes. **Jobbeier** er snapshot lagret på selve jobben. De to kan være forskjellige. Run-loggen skal ikke omskrive jobbeieren dersom en annen bruker kjører jobben.

Dette identitetslaget er generisk. PREMIS er ett mulig proveniensformat; overordnet kjørelogg og framtidige formater som CSV/JSON skal kunne bruke samme runtime-/jobbidentitet uten å avhenge av PREMIS.

Detaljert operasjonslogg og PREMIS forblir knyttet til jobb/output.

## Tilbake til standardmappe

I Innstillinger har de tre konfigurerbare standardmappene knappene `Velg…` og `Bruk standard`.

`Bruk standard` tømmer den eksplisitte konfigurasjonsverdien. Den effektive mappen blir da:

- kjørelogg: `<temp_dir>/logs/runs`
- setup: `<temp_dir>/setup`
- jobblister: `<temp_dir>/joblists`

Workspace-strukturen opprettes ved oppstart og etter endring av `temp_dir`.

Ved åpning/lagring av jobblister brukes den effektive `job_list_dir` som standardlokasjon. Setup eksport/import bruker den effektive `setup_dir`.

## Robusthet ved eldre/importerte jobblister

En jobb med lagret status `Kjører` kan ikke ha en levende worker etter at jobblista er lastet inn på nytt. Før ny kjøring normaliseres derfor stale `RUNNING` til `Klar`. Ugyldig execution cursor fra eldre/importerte data normaliseres også defensivt.

Den overordnede run-loggen opprettes før første jobb starter og har eksplisitt run-status. Dersom batch-worker feiler før første jobb, skal loggen fortsatt avsluttes med `Status: FEIL`, sluttid og feilmelding. Dermed kan en ufullført logg skilles fra en faktisk pågående kjøring.

## Batchfaser og limbo-diagnostikk

Den overordnede run-loggen registrerer aktuell batchfase. Eksempler:

- `Batch opprettet - worker ikke startet ennå`
- `Worker startet`
- `Forbereder JOB-001`
- `Registrerer JOB-001 i kjørelogg`
- `Kjører JOB-001`
- `Avslutter batch`

Dersom ingen jobb registreres innen startup-timeout, utløses en failsafe. Run-loggen avsluttes med feil og GUI-et frigjøres fra permanent `batch_running=True`. En levende Python-tråd tvangsavsluttes ikke; `batch_cancel_requested` settes i stedet slik at kjøringen kan avbrytes så snart worker kommer videre.

## Tekstlig run-logg som sink

Fra a18 er den menneskelesbare overordnede `.log`-filen også flyttet bak den generiske event-grensen.

`RunOverviewLog` beholdes som kompatibilitetsfasade for eksisterende runtime-kall, men formattering og persistens ligger i `TextRunLogSink`. Fasaden oversetter etablerte kall som `start_job()`, `finish_job()`, `set_phase()`, `fail()` og `finish()` til formatnøytrale `WorkflowEvent`-hendelser.

Dette betyr at den operative tekstloggen ikke lenger er en særskilt runtime-modell. Nye loggformater skal implementeres som egne sinks over de samme hendelsene, ikke ved å kopiere logikk fra `RunOverviewLog`.

## Konfigurerbare sinks

Fra z18.7 brukes samme `build_event_dispatcher()`-grense for både run-level og operation-level events. `scope` bestemmer hvilke sinks som er relevante, mens eventmodellen og dispatcher-kontrakten er den samme.

Konfigurasjonen `enabled_log_sinks` beskriver valgte output-adaptere. Dagens registrerte sinks er:

- `text_run_log` – menneskelesbar overordnet kjørelogg
- `premis` – PREMIS-proveniens for relevante operasjonshendelser

Den eldre `enable_premis_provenance` beholdes som kompatibilitetsinnstilling under migreringen. Nye formater som CSV eller JSON skal registreres som nye sinks i komposisjonslaget, ikke bygges inn i executor eller jobbrunner.
