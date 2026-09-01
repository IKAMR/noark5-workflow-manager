# Command-Line Interface (CLI)

`n5wf` er kommandolinjegrensesnittet til Noark 5 Workflow Manager.

CLI-et er laget for kjøring uten GUI, blant annet fra PowerShell, CMD, Windows Terminal, BAT-/PowerShell-skript og automatiserte kjøremiljøer. GUI og CLI skal bruke de samme underliggende jobb-, preflight- og kjørekomponentene.

## Installasjon

Kjør fra rotmappen til Noark 5 Workflow Manager:

```bat
install.bat
```

Installasjonen installerer avhengigheter og registrerer `n5wf` som console command.

Etter installasjon bør en ny PowerShell-, CMD- eller Windows Terminal-økt kunne kjøre:

```text
n5wf --help
n5wf --version
```

Hvis `n5wf` ikke finnes i `PATH`, kan CLI-et brukes direkte via Python launcher som fallback:

```text
py -m noark5_workflow.cli --help
```

Dette er primært en fallback for feilsøking. Den normale brukerkommandoen er `n5wf`.

## Kommandooversikt

### Hjelp

```text
n5wf --help
```

Viser tilgjengelige kommandoer og argumenter.

### Versjon

```text
n5wf --version
```

Viser installert versjon av Noark 5 Workflow Manager CLI.

## Jobblister

CLI-et i v0.1.2-a7 arbeider med eksisterende `.n5jobs`-jobblister.

### Kontrollere en jobbliste

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

### Kjøre en jobbliste

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

### Eksplisitt ny kjøring

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

## Omfang i v0.1.2-a7

Følgende offentlige CLI-kall er implementert i a7:

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
