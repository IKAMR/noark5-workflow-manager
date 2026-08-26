# Noark 5 Workflow Manager

Arbeidsflytverktøy og GUI for analyse, validering og behandling av Noark 5-uttrekk.

Prosjektet følger de arkitektoniske prinsippene i **SIARD Workflow Manager**: operasjoner er skilt fra GUI-et, operasjoner returnerer strukturerte resultater, og arbeidsflytlaget kan utvikles uavhengig av formatspesifikke funksjoner.

**Versjon:** `0.1.0-a1`  
**Status:** første skall / arkitekturprototype

## Formål

Første versjon etablerer et rammeverk som senere kan brukes til blant annet:

- analyse av `arkivstruktur.xml`
- samlede tellinger tilsvarende U1 / N5.101
- tellinger per arkivdel tilsvarende U2 / N5.102
- analyse på tvers av flere Noark 5 XML-filer
- kontroll av dokumentmetadata mot filer i `dokumenter/`
- rapportering og kvalitetskontroll
- lokal eller senere serverbasert kjøring av operasjoner

Selve U1/U2-analysemotoren er ikke implementert i denne første skallversjonen.

## Innhold i første skall

- CustomTkinter-basert skrivebords-GUI
- valg og deteksjon av Noark 5-uttrekk
- operasjonsregister
- kontrakt med `BaseOperation` og `OperationResult`
- `OperationContext` for kilde, innstillinger, fremdrift og arbeidsmappe
- lokal kjøring gjennom `LocalExecutor`
- eksplisitt grensesnitt for fremtidig serverkjøring gjennom `RemoteExecutor`
- operasjon for deteksjon av Noark 5-uttrekk
- enkel inventaroperasjon for metadatafiler
- plassholder for fremtidig strømmet analyse av `arkivstruktur.xml`
- grunnleggende tester

## Noark 5-kilder

Skallet kjenner igjen blant annet:

- `arkivstruktur.xml`
- `arkivuttrekk.xml`
- `loependeJournal.xml`
- `offentligJournal.xml`
- `endringslogg.xml`
- øvrige XML-filer, inkludert virksomhetsspesifikke metadata
- XSD-filer
- `dokumenter/`

## Krav

- Python 3.10 eller nyere
- Windows, macOS eller Linux

Installer avhengigheter:

```bash
pip install -r requirements.txt
```

## Kjøring

```bash
python main.py
```

På Windows kan også `start.bat` brukes.

## Operasjoner

En operasjon arver fra `BaseOperation` og implementerer:

```python
run(ctx) -> OperationResult
```

En operasjon kan i tillegg kontrollere om den kan kjøres gjennom `can_run(ctx)`.

Operasjoner angir et `ExecutionTarget`:

- `local`
- `server`
- `either`

I denne første versjonen brukes bare `LocalExecutor`. `RemoteExecutor` er med som et eksplisitt grensesnitt for senere klient/server-støtte.

## Server/klient-retning

Arkitekturen er bevisst skilt mellom GUI, operasjoner og kjørebackend. En fremtidig klient skal derfor kunne sende samme operasjon til en server eller arbeidsnode, samtidig som lokal kjøring fortsatt er tilgjengelig.

For store bevaringsuttrekk er anbefalt modell **delt lagring + jobbreferanser**, ikke opplasting av hele uttrekket gjennom GUI-klienten.

Se [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for mer informasjon.

## Lisens

GNU General Public License v3. Se `LICENCE`.
