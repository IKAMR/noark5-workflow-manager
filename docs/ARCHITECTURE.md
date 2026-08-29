# Arkitektur

## Mål

Noark 5 Workflow Manager skal være et arbeidsflytramverk for analyse, validering og behandling av komplette Noark 5-uttrekk.

Arkitekturen skiller mellom:

1. **GUI** – valg av uttrekk og operasjoner, fremdrift og resultater.
2. **Kilde-/kontekstmodell** – beskriver Noark 5-uttrekket og hvilke kilder som finnes.
3. **Operasjoner** – avgrensede funksjoner som analyserer eller behandler uttrekket.
4. **Kjørebackend** – bestemmer hvor en operasjon faktisk kjøres.
5. **Logging/proveniens** – vanlig workflow-logg for alle steg og sentral PREMIS-proveniens for relevante hendelser.

Dette skillet gjør det mulig å beholde samme operasjonsmodell når serverkjøring senere innføres.

## Bevaringsprinsipp for Noark 5-kilden

Mottatt Noark 5-uttrekk betraktes som bevis. Analyse, validering og kontroll skal som hovedregel være read-only. Dersom fremtidige operasjoner lager konverterte eller avledede representasjoner, skal original og avledet objekt skilles tydelig og dokumenteres.

DIAS SIP/AIC er et separat pakkenivå. Pakking kan beskrive og supplere pakken uten å omskrive kildeuttrekket.

## Workflow-logg, rapporter og PREMIS

Tre dokumentasjonslag skal holdes adskilt:

- **Workflow-/kjørelogg:** teknisk og operativ historikk.
- **Menneskelesbare rapporter:** kontroll-, analyse- og innholdsrapporter.
- **PREMIS-proveniens:** maskinlesbar proveniens for relevante bevarings-/valideringshendelser.

PREMIS-mekanismen ligger sentralt i `noark5_workflow/core/premis_logger.py`. Operasjoner produserer ikke PREMIS XML selv.

## Kjørebackend

### Nå

- `LocalExecutor`: kjører operasjonen lokalt og håndterer sentral PREMIS-registrering.

### Senere

- `RemoteExecutor`: sender jobber til én eller flere arbeidsflytservere/workere og skal bevare samme logging-/provenienskontrakt.

Operasjoner angir om de kan kjøres `local`, `server` eller `either`.

**Windows desktop er dagens testede kjøremiljø.** Plattformstatus, Windows Server/RDS, Linux, macOS, headless worker/server, web og mobile alternativer dokumenteres i `RUNTIME-ENVIRONMENTS.md`.

## Anbefalt fremtidig servermodell

For store bevaringsuttrekk bør delt lagring brukes fremfor opplasting gjennom klienten:

- klienten velger eller registrerer et uttrekk
- serveren mottar en stabil uttrekks-/lagringsidentifikator
- serveren validerer tilgang og finner riktig lagringssti
- jobben legges i kø og kjøres på en egnet arbeidsnode
- fremdrift og logghendelser sendes tilbake til klienten
- resultatet returnerer strukturerte data og referanser til genererte filer

Senere serverstøtte må blant annet håndtere autentisering, autorisasjon, TLS, varig jobbkø, avbrytelse, gjenopptakelse, arbeidsnodekapasitet, revisjonslogging og isolasjon av filstier.

## Noark 5-kildemodell

Et Noark 5-uttrekk behandles som én logisk kilde med flere deler, blant annet:

- `arkivstruktur.xml`
- `arkivuttrekk.xml`
- `loependeJournal.xml`
- `offentligJournal.xml`
- `endringslogg.xml`
- virksomhetsspesifikke metadata
- XSD-skjemaer
- `dokumenter/`

## Ressurshåndtering og analysemodell

Store XML-kilder bør leses strømmet og gi en strukturert intern resultatmodell som flere rapporter og kontroller kan gjenbruke.

```text
arkivstruktur.xml
        |
        v
strømmet analysemotor
        |
        v
strukturert resultatmodell
   |        |        |
   v        v        v
  U1       U2       QA
```

## Arbeidsområde, AIP-finalisering og AIC

Arbeidsflyten skal skille mellom:

1. **Kilde** – mottatt Noark 5-uttrekk, read-only evidens.
2. **Arbeidsområde** – tester, analysefiler, debug, rapporter, logger og mellomresultater.
3. **AIP-finalisering / AIC-utdata** – eksplisitt kuratert innhold som skal bevares.

Finalisering bør være et eksplisitt workflow-steg. Ingen generert fil skal plasseres i kildeområdet som fallback.

## Bevaringssoner og fremtidig transfermodell

`ORIGINAL_RECEIVED -> QUARANTINE -> WORKING -> FINAL_AIP -> AIC_OUTPUT -> PRESERVATION_STORAGE`

Overføring mellom soner skal være en normal workflow-operasjon med eksplisitt A og B, verifikasjon og relevant PREMIS.

## Eksterne validatorer

Arkade 5 CLI skal kunne kobles inn gjennom en adapter/operasjon som starter programmet, fanger exit status og høster rapporter. Resultatet normaliseres til `OperationResult`.

## Pipeline og recursive jobs

Pipeline er et orkestreringslag over eksisterende operasjoner. Recursive/batch-jobber er et separat orkestreringslag for mange kandidater og skal bruke samme operations/executor-kontrakt.

Se `CODE-MAP.md`, `SHARED-ROADMAP.md`, `JOBS-AND-BATCHES.md`, `JOBS-BATCH-FUTURE-DESIGN.md` og `RUNTIME-ENVIRONMENTS.md`.
