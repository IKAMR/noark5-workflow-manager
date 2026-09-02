# Command-Line Interface (CLI)

`n5wf` er kommandolinjegrensesnittet til Noark 5 Workflow Manager. Det gjør det mulig å kontrollere, lese status for og kjøre eksisterende `.n5jobs`-jobblister uten å starte GUI-et.

## Hurtig bruk

Etter at CLI er installert, åpne en ny PowerShell-, CMD- eller Windows Terminal-økt.

### Kommandoreferanse

| Kommando | Options | Formål |
|---|---|---|
| `n5wf --help` | – | Vis hjelp |
| `n5wf --version` | – | Vis versjon |
| `n5wf jobs check <file.n5jobs>` | – | Kontroller jobblisten uten å kjøre den |
| `n5wf jobs status <file.n5jobs>` | `[--job JOB-ID]` | Vis status for jobblista eller én jobb |
| `n5wf jobs run <file.n5jobs>` | `[--job JOB-ID] [--rerun]` | Kjør hele jobblista eller én valgt jobb |
| `n5wf jobs continue <file.n5jobs>` | `--job JOB-ID` | Fortsett én jobb som venter ved kontrollpunkt |

### Options

`--job JOB-ID`
: Velger én jobb i den angitte `.n5jobs`-jobblista. Gjelder `status` fra v0.1.2-a9, `run` fra v0.1.2-a10 og `continue` fra v0.1.2-a11.

`--rerun`
: Tillater eksplisitt ny kjøring av en valgt eller flere jobber som ellers krever godkjenning. Gjelder `n5wf jobs run`.

Den dokumenterte standardformen er at jobblista står før options:

```text
n5wf jobs status <file.n5jobs> --job JOB-001
n5wf jobs run <file.n5jobs> --job JOB-001
n5wf jobs run <file.n5jobs> --job JOB-001 --rerun
n5wf jobs continue <file.n5jobs> --job JOB-001
```

Options kan også skrives før filargumentet.

### Vanlige eksempler

Kontroller en jobbliste:

```text
n5wf jobs check "G:\arkiv\jobblister\kommune.n5jobs"
```

Vis detaljstatus for én jobb:

```text
n5wf jobs status "G:\arkiv\jobblister\kommune.n5jobs" --job JOB-002
```

Kjør bare én jobb:

```text
n5wf jobs run "G:\arkiv\jobblister\kommune.n5jobs" --job JOB-002
```

Fortsett én jobb som venter ved kontrollpunkt:

```text
n5wf jobs continue "G:\arkiv\jobblister\kommune.n5jobs" --job JOB-002
```

Kjør bare én tidligere ferdig/feilet/hoppet-over jobb på nytt:

```text
n5wf jobs run "G:\arkiv\jobblister\kommune.n5jobs" --job JOB-002 --rerun
```

Kjør hele jobblisten:

```text
n5wf jobs run "G:\arkiv\jobblister\kommune.n5jobs"
```

## Status

Vis status for hele jobblista:

```text
n5wf jobs status <file.n5jobs>
```

Vis detaljert status for én jobb:

```text
n5wf jobs status <file.n5jobs> --job <job-id>
```

`status` er read-only: kommandoen kjører ikke preflight-normalisering og lagrer ikke jobblista. Visningen er en statuslesing av den persistente `.n5jobs`-modellen, ikke live overvåking av en annen kjørende prosess.

Når en tidligere kjørt jobb er redigert og derfor er klar for en ny kjøring, vises status som `Klar – endret etter kjøring` i både jobbliste- og enkeltjobbvisning. Dette er en brukerrettet presisering av `Klar`; CLI-et viser samtidig om eksplisitt rerun-godkjenning kreves og hvorfor.

En jobb-ID som `JOB-001` er foreløpig bare entydig innen den aktuelle `.n5jobs`-fila. Derfor må jobblista inngå i adresséringen.

## Installasjon

Fra v0.1.2-a8 kan CLI installeres alene eller sammen med GUI. Bruk `install.bat`, eller direkte `install.bat all` / `install.bat cli`.

## Kontrollere en jobbliste

```text
n5wf jobs check <file.n5jobs>
```

`check` kjører GUI-uavhengig preflight og kjører ikke jobbene.

## Kjøre jobber

Hele jobblista:

```text
n5wf jobs run <file.n5jobs>
```

Én valgt jobb fra jobblista:

```text
n5wf jobs run <file.n5jobs> --job <job-id>
```

Selektiv kjøring bruker `JobRunner` direkte for den valgte jobben. Andre jobber i jobblista kjøres ikke og skal ikke få endret status som følge av kjøringen.

Preflight for valgt jobb kontrollerer den valgte jobbens rerun-status og kontrollerer dens output mot øvrige jobber i samme jobbliste. En output-konflikt som involverer den valgte jobben blokkerer kjøringen.

Hvis valgt jobb allerede er `Ferdig`, `Feil` eller `Hoppet over`, kreves eksplisitt `--rerun`.

Det samme gjelder en tidligere kjørt jobb som senere er redigert og derfor igjen står som `Klar`. CLI-et forklarer da at konfigurasjonen er endret etter tidligere kjøring. `Klar` beskriver gjeldende execution-state; `--rerun` beskytter historikken fra tidligere kjøring.

For detaljert `jobs status ... --job` vises også om rerun-godkjenning kreves og hvorfor.

Eksempel:

```text
n5wf jobs run <file.n5jobs> --job <job-id> --rerun
```

## Fortsette fra kontrollpunkt

Fra v0.1.2-a11 kan en bestemt jobb som står `Venter ved kontrollpunkt` fortsettes eksplisitt:

```text
n5wf jobs continue <file.n5jobs> --job <job-id>
```

`continue` bruker den persistente execution cursoren og starter ved neste operasjon etter det kontrollpunktet som jobben faktisk venter ved. Allerede fullførte operasjoner kjøres ikke på nytt.

Kommandoen er bare gyldig når jobben står `Venter ved kontrollpunkt`, cursoren peker på en gjenværende operasjon og ventetilstanden er forankret i et reelt kontrollpunkt i workflowen. Ellers avvises fortsettelsen som en ugyldig kjøretilstand.

Hvis jobben møter et nytt kontrollpunkt, lagres den nye cursoren og kommandoen returnerer exit code `5`. Hvis workflowen fullføres, returneres `0`.

Både CLI og GUI bruker samme eksplisitte `JobRunner.continue_job()`-kontrakt. Selve execution-logikken gjenbruker ordinær `JobRunner.run()` etter at continue-tilstanden er validert.

Kjøring og fortsettelse lagrer oppdatert status for den valgte jobben tilbake i samme `.n5jobs`-fil og setter den som aktiv jobb.

## Exit codes

| Exit code | Betydning |
|---:|---|
| `0` | Kommandoen ble fullført uten feil |
| `2` | Ugyldig kommando eller ugyldige argumenter |
| `3` | Preflight feilet, kjøring krever eksplisitt godkjenning eller `continue` ble avvist fordi jobben ikke kan fortsettes |
| `4` | Jobb-/batchkjøringen feilet |
| `5` | En eller flere jobber / valgt jobb venter ved kontrollpunkt |
| `6` | Etterspurt jobb-ID finnes ikke i angitt jobbliste |

## GUI og CLI

GUI-et startes med `start.bat`. CLI-et startes med `n5wf ...`. De bruker samme underliggende jobb-/workflowmodell.

## Omfang

Følgende offentlige CLI-kall er implementert per v0.1.2-a11:

```text
n5wf --help
n5wf --version
n5wf jobs check <file.n5jobs>
n5wf jobs status <file.n5jobs>
n5wf jobs status <file.n5jobs> --job <job-id>
n5wf jobs run <file.n5jobs>
n5wf jobs run <file.n5jobs> --rerun
n5wf jobs run <file.n5jobs> --job <job-id>
n5wf jobs run <file.n5jobs> --job <job-id> --rerun
n5wf jobs continue <file.n5jobs> --job <job-id>
```

CLI-et oppretter eller redigerer foreløpig ikke jobber/jobblister fra kommandolinjen. En egen offentlig `stop`-kommando er ikke implementert.

## Videre CLI-/styringsdesign

Videre planlagt programmatisk styring og mulige framtidige CLI-kommandoer/options er beskrevet i `INTERFACE.md`. Overordnet framtidsdesign for jobb-, batch- og workflowstyring er beskrevet i `JOBS-BATCH-FUTURE-DESIGN.md`.

Ved analyse av videre CLI-utvikling skal `CLI.md` og `INTERFACE.md` leses sammen; ved funksjonelle jobb-/batch-/workflowendringer skal også `JOBS-BATCH-FUTURE-DESIGN.md` kontrolleres.

## Dokumentasjonsregel

Denne filen er den autoritative brukerreferansen for det offentlige `n5wf`-grensesnittet.
