# Command-Line Interface (CLI)

`n5wf` er kommandolinjegrensesnittet til Noark 5 Workflow Manager. Det gjør det mulig å kontrollere og kjøre eksisterende `.n5jobs`-jobblister uten å starte GUI-et.

## Hurtig bruk

Etter at CLI er installert, åpne en ny PowerShell-, CMD- eller Windows Terminal-økt.

### Kommandoreferanse

| Kommando | Options | Formål |
|---|---|---|
| `n5wf --help` | – | Vis hjelp |
| `n5wf --version` | – | Vis versjon |
| `n5wf jobs check <file.n5jobs>` | – | Kontroller jobblisten uten å kjøre den |
| `n5wf jobs run <file.n5jobs>` | `[--rerun]` | Kjør jobblisten |

### Options

`--rerun`
: Tillater eksplisitt ny kjøring av jobber som ellers krever godkjenning. Gjelder `n5wf jobs run`.

Den kan skrives både etter og før filargumentet. Den dokumenterte standardformen er:

```text
n5wf jobs run <file.n5jobs> --rerun
```

Følgende form er også gyldig:

```text
n5wf jobs run --rerun <file.n5jobs>
```

`<file.n5jobs>` er et obligatorisk posisjonelt argument til `run`; det er ikke definert som en generell «parameter 3».

### Vanlige eksempler

Kontroller en jobbliste:

```text
n5wf jobs check "G:\arkiv\jobblister\kommune.n5jobs"
```

Kjør jobblisten:

```text
n5wf jobs run "G:\arkiv\jobblister\kommune.n5jobs"
```

Kjør den på nytt når rerun-godkjenning kreves:

```text
n5wf jobs run "G:\arkiv\jobblister\kommune.n5jobs" --rerun
```

Detaljer om kontroll, kjøring, exit codes og automatisering står nedenfor.

## Installasjon

Fra v0.1.2-a8 kan CLI installeres alene eller sammen med GUI.

Interaktivt fra rotmappen til Noark 5 Workflow Manager:

```bat
install.bat
```

Velg `GUI + CLI` eller `CLI`. Installasjonen kan også startes direkte uten meny:

```bat
install.bat all
install.bat cli
```

Core er en felles logisk komponent for GUI og CLI. Installer lagrer per-user profilstatus slik at senere installasjon eller deinstallasjon av GUI/CLI ikke unødvendig fjerner den andre profilen.

CLI-installasjonen oppretter en stabil `n5wf`-launcher og registrerer launcher-mappen i brukerens Windows `PATH`.

Hvis `n5wf` ikke finnes i `PATH`, kan CLI-et brukes direkte via Python launcher som fallback:

```text
py -m noark5_workflow.cli --help
```

Dette er primært en fallback for feilsøking. Den normale brukerkommandoen er `n5wf`.

### Deinstallasjon av CLI

CLI kan fjernes med:

```bat
deinstall.bat cli
```

eller gjennom den interaktive menyen i `deinstall.bat`. Deinstallasjon krever eksplisitt `Ja` før den utføres.

Dersom GUI fortsatt er registrert installert, beholdes Core-status. Deinstallasjon fjerner ikke jobblister, logger, config, repository eller generelle Python-pakker som kan være delt med andre programmer.

## Kontrollere en jobbliste

```text
n5wf jobs check <file.n5jobs>
```

Eksempel:

```text
n5wf jobs check "G:\arkiv\jobblister\kommune.n5jobs"
```

Kommandoen:

- leser jobblisten
- kjører GUI-uavhengig preflight
- normaliserer sikre tilstander der dette er støttet
- kontrollerer konflikter mellom output-mapper
- identifiserer jobber som krever eksplisitt godkjenning for ny kjøring
- kjører ikke jobbene

## Kjøre en jobbliste

```text
n5wf jobs run <file.n5jobs>
```

Eksempel:

```text
n5wf jobs run "G:\arkiv\jobblister\kommune.n5jobs"
```

Kommandoen:

1. leser `.n5jobs`
2. kjører preflight
3. stopper hvis preflight finner blokkerende feil
4. stopper hvis jobber krever eksplisitt rerun-godkjenning
5. kjører jobbene sekvensielt via den samme kjernelogikken som GUI-et
6. oppdaterer jobblisten under kjøringen
7. skriver overordnet kjørelogg
8. returnerer en exit code som kan brukes av skript og andre systemer

Kjøreveien er:

```text
CLI
 |
 +--> JobPreflight
       |
       +--> BatchRunner
             |
             +--> JobRunner
                   |
                   +--> LocalExecutor
```

CLI-et implementerer dermed ikke en separat workflow-motor.

## Eksplisitt ny kjøring

Hvis jobblisten inneholder jobber som allerede har nådd en terminal status, må ny kjøring godkjennes eksplisitt:

```text
n5wf jobs run <file.n5jobs> --rerun
```

Eksempel:

```text
n5wf jobs run "G:\arkiv\jobblister\kommune.n5jobs" --rerun
```

`--rerun` gjør det mulig å kjøre slike jobber på nytt uten et GUI-spørsmål. Dette er nødvendig fordi CLI-et skal kunne brukes uten interaktiv dialog.

## Exit codes

CLI-et bruker exit codes slik at BAT-, PowerShell- og andre systemer kan avgjøre resultatet av kommandoen.

| Exit code | Betydning |
|---:|---|
| `0` | Kommandoen ble fullført uten feil |
| `2` | Ugyldig kommando eller ugyldige argumenter |
| `3` | Preflight feilet eller kjøring krever eksplisitt godkjenning |
| `4` | Jobb-/batchkjøringen feilet |
| `5` | En eller flere jobber venter ved kontrollpunkt |

Eksempel i BAT:

```bat
n5wf jobs check "D:\jobs\nightly.n5jobs"
if errorlevel 1 exit /b %errorlevel%

n5wf jobs run "D:\jobs\nightly.n5jobs"
```

## GUI og CLI

GUI-et startes som før:

```bat
start.bat
```

CLI-et startes med:

```text
n5wf ...
```

De er to innganger til samme applikasjon:

```text
start.bat                         GUI
n5wf jobs check <file.n5jobs>     CLI preflight
n5wf jobs run <file.n5jobs>       CLI execution
```

En jobb eller jobbliste skal kunne kontrolleres og kjøres fra CLI uten at GUI-et er startet.

## Kommando- og navnekonvensjoner

CLI-kommandoer, subcommands, argumentnavn og flags skal være korte, presise og på engelsk.

Eksempler:

```text
jobs
check
run
--rerun
```

Brukerrettet status- og loggtekst kan være norsk selv om den stabile maskinrettede kommandosyntaksen er engelsk.

## Omfang

Følgende offentlige CLI-kall er implementert fra v0.1.2-a7:

```text
n5wf --help
n5wf --version
n5wf jobs check <file.n5jobs>
n5wf jobs run <file.n5jobs>
n5wf jobs run <file.n5jobs> --rerun
```

CLI-et oppretter eller redigerer foreløpig ikke jobber/jobblister fra kommandolinjen. Første CLI-versjon er bevisst begrenset til kontroll og kjøring av eksisterende `.n5jobs`-jobblister.

## Dokumentasjonsregel

Denne filen er den autoritative brukerreferansen for det offentlige `n5wf`-grensesnittet.

Når nye CLI-kommandoer, subcommands, argumenter, flags eller exit codes blir offentlig støttet, skal de dokumenteres her.
