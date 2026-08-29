# Noark 5 Workflow Manager

Arbeidsflytverktøy og GUI for analyse, validering og behandling av Noark 5-uttrekk.


## Forhold til SIARD Workflow Manager

Noark 5 Workflow Manager bygger på arkitektur, arbeidsflytmodell, GUI-prinsipper og enkelte generelle funksjonelle konsepter fra [SIARD Workflow Manager](https://github.com/smult/SIARD-Workflow-Manager).

Prosjektene er separate verktøy for henholdsvis Noark 5- og SIARD-uttrekk. Noark 5-spesifikk analyse og SIARD-spesifikk behandling holdes adskilt, mens generelle arbeidsflyt- og pakkekonsepter kan følge samme modell der dette er naturlig.

## Viktig prinsipp: uttrekk og DIAS-pakke er separate nivåer

Noark 5 er system-/uttrekksnivået. DIAS SIP/AIC er pakkenivået rundt innholdet.

DIAS-pakking skal ikke endre, omorganisere eller tolke om den interne strukturen i Noark 5-uttrekket. Det valgte uttrekket pakkes som innhold med uendret intern struktur, mens DIAS-laget beskriver og kontrollerer pakken gjennom blant annet METS, PREMIS, sjekksummer og pakkeidentifikatorer.

## Status

Programmet har blant annet:

- CustomTkinter-basert desktop-GUI
- valg og automatisk deteksjon av Noark 5-uttrekk
- kategorisert operasjonspalett og workflow
- lokal kjøring gjennom `LocalExecutor`
- eksplisitt grensesnitt for framtidig serverkjøring gjennom `RemoteExecutor`
- Job/Batch-modell med flere isolerte jobber
- sekvensiell `Start alle`
- separat workflow, operasjonsparametre og output per jobb
- output/resource locking
- vedvarende `.n5jobs`-jobblister
- automatisk per-user arbeidsstatus for gjeldende jobb/jobbliste
- kontroll av source-/target-kollisjoner og tidligere Workflow Manager-output
- DIAS SIP/AIC-pakking
- import av eksisterende METS XML / `info.xml`
- SHA-256, METS, PREMIS, `info.xml`, `log.xml` og ukomprimert SIP TAR
- `Legg til fil`, `Legg til mappe` og `Opprett mappe`
- sentral workflow-PREMIS
- vedvarende sist brukte mapper
- `test.bat` med rapport til `docs/test-results/`

Se `docs/JOBS-AND-BATCHES.md` og `docs/JOBS-BATCH-FUTURE-DESIGN.md` for jobbmodellen og videre retning.

## Kjøremiljø

**Windows desktop er dagens testede og støttede baseline.**

Normal bruk på Windows:

1. Kjør `install.bat` ved første installasjon eller når avhengigheter endres.
2. Kjør `test.bat` og kontroller at alle tester består.
3. Start programmet med `start.bat`.

Python-kjernen er i stor grad plattformuavhengig, og Linux/macOS, Windows RDS/Terminal Server, headless server/worker, webklient og andre miljøer er realistiske framtidige mål. De skal ikke omtales som støttet før de har egne installasjons-/oppstarts-/testløp og er praktisk verifisert.

Se [docs/RUNTIME-ENVIRONMENTS.md](docs/RUNTIME-ENVIRONMENTS.md) for gjeldende status, plattformbindinger og framtidige muligheter.

## Jobber og jobblister

Grunnprinsippet er:

> One job = one source + one workflow + one output area.

Jobblister kan lagres som `.n5jobs`. Store arkivuttrekk bygges ikke inn i jobblistefilen; kilde og output refereres med plassering.

Gjeldende ikke-manuelt-lagrede arbeidsstatus kan lagres automatisk per bruker utenfor repository/installasjonsmappen slik at arbeid kan gjenopprettes etter ny programstart.

## Workflow logging og PREMIS-proveniens

Alle operasjoner/tester vises i vanlig workflow-/kjørelogg. Relevante bevarings-/valideringshendelser kan i tillegg registreres som PREMIS events.

Operasjoner skriver ikke workflow-PREMIS XML selv. `LocalExecutor` bruker den sentrale loggeren. Genererte workflow-filer skal skrives til eksplisitt arbeids-/utdataområde og ikke inn i mottatt Noark 5-kilde.

## DIAS-pakking

DIAS-dialogen kan lese metadata fra eksisterende METS/`info.xml` og supplere pakken med manuelt valgte filer, mapper og nye tomme mapper.

Tilleggsinnhold pakkes fra valgt kilde uten å endre originalmaterialet på disk.

## Krav

- Python 3.10 eller nyere
- Windows desktop er dagens testede baseline
- Python-avhengigheter installeres via `install.bat` / `requirements.txt`

Se `docs/RUNTIME-ENVIRONMENTS.md` før andre kjøremiljøer beskrives eller gjøres til støttede plattformer.

## Operasjonsarkitektur

En operasjon arver fra `BaseOperation` og implementerer:

```python
run(ctx) -> OperationResult
```

Operasjoner angir et `ExecutionTarget`:

- `local`
- `server`
- `either`

I dagens implementasjon brukes `LocalExecutor`. `RemoteExecutor` er arkitekturgrensen for senere klient/server-støtte.

For store bevaringsuttrekk er anbefalt framtidig servermodell delt lagring + jobbreferanser, ikke opplasting av hele uttrekket gjennom GUI-klienten.

Se [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Testing

`test.bat` kjører automatiserte tester og skriver versjonert rapport under `docs/test-results/`.

Se [docs/TESTING.md](docs/TESTING.md).

## Utviklingsdokumentasjon

Før større endringer, se:

- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/INTERFACE.md](docs/INTERFACE.md)
- [docs/DEFINITIONS.md](docs/DEFINITIONS.md)
- [docs/CODE-MAP.md](docs/CODE-MAP.md)
- [docs/SHARED-DEVELOPMENT.md](docs/SHARED-DEVELOPMENT.md)
- [docs/SHARED-ROADMAP.md](docs/SHARED-ROADMAP.md)
- [docs/RUNTIME-ENVIRONMENTS.md](docs/RUNTIME-ENVIRONMENTS.md)
- [docs/RELEASES.md](docs/RELEASES.md)

## Releasehistorikk

Ferdige versjoner dokumenteres samlet i [docs/RELEASES.md](docs/RELEASES.md). Interne alpha-/fikstrinn beholdes ikke som separate permanente releasefiler.

## Lisens

GNU General Public License v3. Se `LICENCE`.
