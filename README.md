# Noark 5 Workflow Manager

Arbeidsflytverktøy for analyse, validering og behandling av Noark
5-uttrekk. Programmet har et CustomTkinter-basert desktop-GUI og fra
v0.1.2-a7 også et lokalt CLI-grensesnitt (`n5wf`) for headless kontroll
og kjøring av eksisterende jobblister. Jobb-, workflow- og
operasjonslogikken holdes uavhengig av grensesnittet, slik at GUI, CLI og
senere server-/API-grensesnitt kan bruke samme underliggende modell.

## Forhold til SIARD Workflow Manager

Noark 5 Workflow Manager bygger på arkitektur, arbeidsflytmodell,
GUI-prinsipper og enkelte generelle funksjonelle konsepter fra [SIARD
Workflow Manager](https://github.com/smult/SIARD-Workflow-Manager).

Prosjektene er separate verktøy for henholdsvis Noark 5- og
SIARD-uttrekk. Noark 5-spesifikk analyse og SIARD-spesifikk behandling
holdes adskilt, mens generelle arbeidsflyt- og pakkekonsepter kan følge
samme modell der dette er naturlig.

## Viktig prinsipp: uttrekk og DIAS-pakke er separate nivåer

Noark 5 er system-/uttrekksnivået. DIAS SIP/AIC er pakkenivået rundt
innholdet.

DIAS-pakking skal som hovedregel ikke endre, omorganisere eller tolke om
den interne strukturen i Noark 5-uttrekket. Det valgte uttrekket pakkes
som innhold med uendret intern struktur, mens DIAS-laget beskriver og
kontrollerer pakken gjennom blant annet METS, PREMIS, sjekksummer og
pakkeidentifikatorer.

Når mottatt struktur må normaliseres for workflow-/bevaringsstrategi
eller verktøykompatibilitet, skal repakking være en eksplisitt og
dokumentert transformasjon. Original mottatt SIP/TAR skal som hovedregel
bevares urørt.

## Status

Programmet har blant annet:

-   CustomTkinter-basert desktop-GUI
-   lokal CLI (`n5wf`) for kontroll og kjøring av eksisterende `.n5jobs`-jobblister
-   valg og automatisk deteksjon av Noark 5-uttrekk
-   kategorisert operasjonspalett og workflow
-   lokal kjøring gjennom `LocalExecutor`
-   eksplisitt grensesnitt for framtidig serverkjøring gjennom
    `RemoteExecutor`
-   Job/Batch-modell med flere isolerte jobber
-   GUI-uavhengig `JobPreflight`, `JobRunner` og `BatchRunner`
-   sekvensiell `Start alle`
-   separat workflow, operasjonsparametre og output per jobb
-   output/resource locking
-   vedvarende `.n5jobs`-jobblister
-   automatisk per-user arbeidsstatus for gjeldende jobb/jobbliste
-   kontroll av source-/target-kollisjoner og tidligere Workflow
    Manager-output
-   DIAS SIP/AIC-pakking
-   import av eksisterende METS XML / `info.xml`
-   SHA-256, METS, PREMIS, `info.xml`, `log.xml` og ukomprimert SIP TAR
-   `Legg til fil`, `Legg til mappe` og `Opprett mappe`
-   sentral workflow-PREMIS
-   vedvarende sist brukte mapper
-   `test.bat` med rapport til `docs/test-results/`

CLI-et i v0.1.2-a7 er bevisst avgrenset til kontroll og kjøring av
eksisterende jobblister. Oppretting/redigering av jobber fra CLI,
fortsettelse/stopp som egne CLI-kommandoer og senere server-/API-styring
er videre utviklingsretning.

Se [docs/CLI.md](docs/CLI.md) for den autoritative CLI-referansen og
`docs/JOBS-AND-BATCHES.md` / `docs/JOBS-BATCH-FUTURE-DESIGN.md` for
jobbmodellen og videre retning.

## Kjøremiljø

**Windows desktop er dagens testede og støttede baseline. Lokal `n5wf`
CLI er også praktisk verifisert på Windows.**

Fra v0.1.2-a8 kan Windows-installasjonen velges som `GUI + CLI`, `GUI`
eller `CLI`. Core er en felles logisk komponent og holdes aktiv så lenge
minst ett av grensesnittene er registrert installert. `install.bat` og
`deinstall.bat` lagrer denne statusen per bruker under `%LOCALAPPDATA%`.
Generelle Python-pakker avinstalleres ikke automatisk, siden de kan være
delt med andre Python-programmer.

Normal bruk på Windows:

1.  Kjør `install.bat` ved første installasjon eller når avhengigheter
    endres. Velg GUI + CLI, GUI eller CLI.
2.  Kjør `test.bat` og kontroller at alle tester består.
3.  Start GUI med `start.bat`, eller bruk CLI med `n5wf ...`.

Installasjonen kan også styres uten meny:

```text
install.bat all
install.bat gui
install.bat cli
```

Deinstallasjon bruker tilsvarende `all`, `gui` eller `cli` og krever
eksplisitt `Ja` før den utføres.

Eksempler:

```text
n5wf --help
n5wf jobs check <file.n5jobs>
n5wf jobs run <file.n5jobs>
```

Python-kjernen er i stor grad plattformuavhengig. Linux/macOS,
Windows RDS/Terminal Server, headless server/worker, webklient og andre
miljøer er realistiske framtidige mål. De skal ikke omtales som støttet
før relevante installasjons-/oppstarts-/testløp er etablert og praktisk
verifisert.

Se [docs/RUNTIME-ENVIRONMENTS.md](docs/RUNTIME-ENVIRONMENTS.md) for
gjeldende status, plattformbindinger og framtidige muligheter.

## Jobber og jobblister

Grunnprinsippet er:

> One job = one source + one workflow + one output area.

Jobblister kan lagres som `.n5jobs`. Store arkivuttrekk bygges ikke inn
i jobblistefilen; kilde og output refereres med plassering.

Gjeldende ikke-manuelt-lagrede arbeidsstatus kan lagres automatisk per
bruker utenfor repository/installasjonsmappen slik at arbeid kan
gjenopprettes etter ny programstart.

Jobb- og jobblistemodellen er ikke avhengig av desktop-GUI-et. GUI og
den implementerte CLI-en bruker samme underliggende jobb-, workflow- og
executorlag. Eventuelle senere API-klienter skal bygge videre på samme
modell.

## Workflow logging og PREMIS-proveniens

Alle operasjoner/tester vises i vanlig workflow-/kjørelogg. Relevante
bevarings-/valideringshendelser kan i tillegg registreres som PREMIS
events.

Operasjoner skriver ikke workflow-PREMIS XML selv. `LocalExecutor`
bruker den sentrale loggeren. Genererte workflow-filer skal skrives til
eksplisitt arbeids-/utdataområde og ikke inn i mottatt Noark 5-kilde.

## DIAS-pakking

DIAS-dialogen kan lese metadata fra eksisterende METS/`info.xml` og
supplere pakken med manuelt valgte filer, mapper og nye tomme mapper.

Tilleggsinnhold pakkes fra valgt kilde uten å endre originalmaterialet
på disk.

DIAS-metadata og DIAS-pakken er et eget pakkenivå rundt Noark
5-uttrekket. Eksisterende Noark 5-TAR skal kunne leses direkte der
analyse eller validering ikke krever fysisk uttrekking av hele
innholdet. Detaljene og grensene for normalisering/repakking beskrives i
`docs/ARCHITECTURE.md`.

## Krav

-   Python 3.10 eller nyere
-   Windows desktop er dagens testede baseline
-   lokal `n5wf` CLI er praktisk verifisert på Windows
-   Python-avhengigheter installeres via `install.bat` og de delte
    requirements-filene i repository-roten

Se `docs/RUNTIME-ENVIRONMENTS.md` før andre kjøremiljøer beskrives eller
gjøres til støttede plattformer.

## Operasjonsarkitektur

En operasjon arver fra `BaseOperation` og implementerer:

```python
run(ctx) -> OperationResult
```

Operasjoner angir et `ExecutionTarget`:

-   `local`
-   `server`
-   `either`

I dagens implementasjon brukes `LocalExecutor`. `RemoteExecutor` er
arkitekturgrensen for senere klient/server-støtte.

GUI-et skal ikke eie domenelogikk som er nødvendig for å opprette, kjøre
eller følge jobber. Den implementerte CLI-en bruker samme delte
Job/Workflow/Executor-kontrakter som GUI-et, og senere API-/servergrensesnitt
skal fortsette dette prinsippet i stedet for å etablere parallelle
workflow-implementasjoner.

For store bevaringsuttrekk er anbefalt framtidig servermodell delt
lagring + jobbreferanser, ikke opplasting av hele uttrekket gjennom
klientgrensesnittet.

Se [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md),
[docs/INTERFACE.md](docs/INTERFACE.md) og [docs/CLI.md](docs/CLI.md).

## Testing

`test.bat` kjører automatiserte tester og skriver versjonert rapport
under `docs/test-results/`.

Se [docs/TESTING.md](docs/TESTING.md).

## Utviklingsdokumentasjon

Før større endringer, se:

-   [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
-   [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
-   [docs/INTERFACE.md](docs/INTERFACE.md)
-   [docs/CLI.md](docs/CLI.md)
-   [docs/DEFINITIONS.md](docs/DEFINITIONS.md)
-   [docs/CODE-MAP.md](docs/CODE-MAP.md)
-   [docs/SHARED-DEVELOPMENT.md](docs/SHARED-DEVELOPMENT.md)
-   [docs/SHARED-ROADMAP.md](docs/SHARED-ROADMAP.md)
-   [docs/RUNTIME-ENVIRONMENTS.md](docs/RUNTIME-ENVIRONMENTS.md)
-   [docs/RELEASES.md](docs/RELEASES.md)

## Releasehistorikk

Ferdige versjoner dokumenteres samlet i
[docs/RELEASES.md](docs/RELEASES.md). Interne alpha-/fikstrinn beholdes
ikke som separate permanente releasefiler.

## Lisens

GNU General Public License v3. Se `LICENCE`.
