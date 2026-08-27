# Noark 5 Workflow Manager

Arbeidsflytverktøy og GUI for analyse, validering og behandling av Noark 5-uttrekk.

**Versjon:** `0.1.0-a10`

## Forhold til SIARD Workflow Manager

Noark 5 Workflow Manager bygger på arkitektur, arbeidsflytmodell, GUI-prinsipper og enkelte generelle funksjonelle konsepter fra [SIARD Workflow Manager](https://github.com/smult/SIARD-Workflow-Manager).

Prosjektene er separate verktøy for henholdsvis Noark 5- og SIARD-uttrekk. Noark 5-spesifikk analyse og SIARD-spesifikk behandling holdes adskilt, mens generelle arbeidsflyt- og pakkekonsepter kan følge samme modell der dette er naturlig.

## Viktig prinsipp: uttrekk og DIAS-pakke er separate nivåer

Noark 5 er system-/uttrekksnivået. DIAS SIP/AIC er pakkenivået rundt innholdet.

DIAS-pakking skal derfor ikke endre, omorganisere eller tolke om den interne strukturen i Noark 5-uttrekket. Det valgte uttrekket pakkes som innhold med uendret intern struktur, mens DIAS-laget beskriver og kontrollerer pakken gjennom blant annet METS, PREMIS, sjekksummer og pakkeidentifikatorer.

Den overordnede DIAS-pakkestrukturen er den samme uavhengig av om innholdet er et Noark 5-uttrekk eller annet arkivmateriale. Metadataelementer og verdier kan naturlig variere med innhold og avlevering.

## Status i v0.1.0-a10

Denne alfaen viderefører GUI- og arbeidsflytskallet fra tidligere versjoner og har nå:

- CustomTkinter-basert skrivebords-GUI
- valg og automatisk deteksjon av Noark 5-uttrekk
- kategorisert operasjonspalett og workflow
- lokal kjøring gjennom `LocalExecutor`
- eksplisitt grensesnitt for fremtidig serverkjøring gjennom `RemoteExecutor`
- vedvarende A-/A+ skriftstørrelse etter samme prinsipp som SIARD Workflow Manager
- metadataoversikt og plassholder for senere arkivstruktur-analyse
- DIAS-pakking (SIP/AIC) av komplett valgt Noark 5-uttrekk
- SHA-256, METS, PREMIS, `info.xml`, `log.xml` og ukomprimert SIP TAR
- DIAS-konfigurasjonsdialog med to-kolonne-oppsett: `METADATA | PAKKESTRUKTUR`
- innlesing av eksisterende METS XML (`info.xml`, `mets.xml` eller annet filnavn)
- validering av obligatoriske DIAS-felt og periodedatoer
- interaktiv pakkevisning med `Legg til fil`, `Legg til mappe`, `Opprett mappe`, `Fjern` og valg av målområde i DIAS-pakken
- ekstra filer og mapper kan legges under `content/`, `administrative_metadata/`, `administrative_metadata/repository_operations/` eller `descriptive_metadata/`
- `test.bat` kjører alle automatiserte tester og skriver versjonert rapport til `docs/test-results/`
- testing er dokumentert i `docs/TESTING.md`
- sist brukte mapper huskes i `config.json` for Noark 5-kilde, DIAS-utdata, METS/info.xml-import, `Legg til fil` og `Legg til mappe`
- sentral PREMIS-proveniens etter samme generiske arkitekturmønster som SIARD Workflow Manager
- relevante operasjoner deklarerer PREMIS-hendelser; `LocalExecutor` registrerer og skriver `<uttrekksnavn>_premis.xml`

U1/N5.101, U2/N5.102 og den virkelige strømmede analysemotoren for `arkivstruktur.xml` er ikke implementert ennå.

## Workflow logging og PREMIS-proveniens

a10 innfører en sentral PREMIS-proveniensmekanisme basert på den generiske `PremisProvenanceLogger`-arkitekturen i SIARD Workflow Manager. Koden er tilpasset Noark 5 som objekt og `Noark 5 Workflow Manager` som programvareagent.

Prinsippet er:

- alle operasjoner/tester vises i vanlig workflow-/kjørelogg
- relevante bevarings-/valideringshendelser kan i tillegg bli PREMIS events
- operasjoner skriver ikke PREMIS XML selv
- `LocalExecutor` bruker den sentrale loggeren og lagrer én samlet `<uttrekksnavn>_premis.xml` ved siden av uttrekksmappen, med mindre `premis_output_dir` er konfigurert
- `enable_premis_provenance=false` kan slå av denne registreringen

`DIAS-pakking (SIP/AIC)` er første konkrete operasjon som registreres som `Creation`. Workflow-PREMIS er separat fra den package-level PREMIS/METS som DIAS-pakkingen allerede lager inne i selve pakken.

Mottatt Noark 5-uttrekk endres ikke for å produsere proveniens.

## Sist brukte mapper

Arbeidsmapper huskes mellom programstarter. Dette er brukerkomfort og lagres i lokal `config.json`; det er ikke en del av et prosjekt eller en DIAS-profil.

Følgende huskes:

- sist valgte rotmappe for Noark 5-uttrekk
- sist valgte utdatamappe for DIAS-pakke
- sist brukte mappe ved innlesing av METS/info.xml
- sist brukte mappe for `Legg til fil`
- sist brukte mappe for `Legg til mappe`

Filvelgerne åpner neste gang i den relevante sist brukte mappen. Eksisterende `config.json` oppgraderes automatisk med standardverdier for nye nøkler.

Profiler er et eget, senere lag for gjenbrukbare workflow- og metadataoppsett og skal ikke blandes sammen med disse sist-brukt-innstillingene.

## Noark 5-kilder

Programmet kjenner igjen blant annet:

- `arkivstruktur.xml`
- `arkivuttrekk.xml`
- `loependeJournal.xml`
- `offentligJournal.xml`
- `endringslogg.xml`
- øvrige XML-filer, inkludert virksomhetsspesifikke metadata
- XSD-filer
- `dokumenter/`

## DIAS-pakking (SIP/AIC)

Velg først et Noark 5-uttrekk. Under kategorien `SIP/AIC-Pakking` kan operasjonen `DIAS-pakking (SIP/AIC)` legges til workflow.

Dialogen kan lese metadata fra en eksisterende METS-fil. Importen tolker blant annet:

- `LABEL` som pakketittel
- `altRecordID TYPE="SUBMISSIONAGREEMENT"`
- `altRecordID TYPE="STARTDATE"`
- `altRecordID TYPE="ENDDATE"`
- METS-agenter for arkivorganisasjon, kildesystem/systemversjon/arkivtype, skaper, produsent, avleverer, eier og bevaringsansvarlig

Noark 5-kilden vises i pakkestrukturen. DIAS-dialogen kan i tillegg supplere pakken med manuelt valgte filer, hele mapper med understruktur, eller nye tomme mapper som opprettes direkte i pakkeoppsettet. Valgt målområde styres i pakkestrukturen, slik at for eksempel rapporter og depotoperasjoner kan plasseres under `administrative_metadata/repository_operations/`, beskrivende materiale under `descriptive_metadata/`, eller tilleggsinnhold under `content/`.

Tilleggsfiler og tilleggsmapper pakkes direkte fra valgt kilde inn i den ukomprimerte SIP-TAR-filen. De kopieres ikke først til en midlertidig staging-mappe. Nye mapper opprettes bare i pakkeoppsettet. Kilder på disk endres ikke.

### Workflow-/prosjektkontroller

Workflow-panelet viser også de samme grunnkontrollene som SIARD Workflow Manager for `Lagre profil...`, `Åpne prosjekt`, `Lagre prosjekt` og prosjekt-reset. Selve profil-/prosjektformatet er ennå ikke implementert i Noark 5 Workflow Manager, så disse knappene er foreløpig deaktivert. Dette unngår å etablere et ufullstendig prosjektformat som senere ikke kan bevare operasjonsparametere korrekt.

## Krav

- Python 3.10 eller nyere
- Windows, macOS eller Linux

På Windows er normal bruk:

1. Kjør `install.bat` ved første installasjon eller når avhengigheter endres.
2. Kjør `test.bat` og kontroller at alle tester består.
3. Start programmet med `start.bat`.

`test.bat` skriver automatisk en versjonert testrapport til `docs/test-results/`. Se [docs/TESTING.md](docs/TESTING.md).

## Operasjonsarkitektur

En operasjon arver fra `BaseOperation` og implementerer:

```python
run(ctx) -> OperationResult
```

En operasjon kan i tillegg kontrollere om den kan kjøres gjennom `can_run(ctx)`.

Operasjoner angir et `ExecutionTarget`:

- `local`
- `server`
- `either`

I dagens versjon brukes `LocalExecutor`. `RemoteExecutor` er et eksplisitt grensesnitt for senere klient/server-støtte.

## Server/klient-retning

Arkitekturen er bevisst skilt mellom GUI, operasjoner og kjørebackend. En fremtidig klient skal kunne sende samme operasjon til en server eller arbeidsnode, samtidig som lokal kjøring fortsatt er tilgjengelig.

For store bevaringsuttrekk er anbefalt modell delt lagring + jobbreferanser, ikke opplasting av hele uttrekket gjennom GUI-klienten.

Se [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for mer informasjon.

## Lisens

GNU General Public License v3. Se `LICENCE`.

## Utviklingsdokumentasjon

Før større endringer, se [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md). Begreper og grensesnitt er dokumentert i [docs/DEFINITIONS.md](docs/DEFINITIONS.md) og [docs/INTERFACE.md](docs/INTERFACE.md).
