# Arkitektur

## Mål

Noark 5 Workflow Manager skal være et arbeidsflytramverk for analyse, validering og behandling av komplette Noark 5-uttrekk.

Arkitekturen skiller mellom:

1. **Bruker-/styringsgrensesnitt** – desktop-GUI og lokal CLI i dag, og senere eksterne grensesnitt mot samme underliggende jobb-/workflowmodell.
2. **Kilde-/kontekstmodell** – beskriver Noark 5-uttrekket og hvilke kilder som finnes.
3. **Operasjoner** – avgrensede funksjoner som analyserer eller behandler uttrekket.
4. **Kjørebackend** – bestemmer hvor en operasjon faktisk kjøres.
5. **Logging/proveniens** – vanlig workflow-logg for alle steg og sentral PREMIS-proveniens for relevante hendelser.

Dette skillet gjør det mulig å beholde samme operasjonsmodell når serverkjøring senere innføres.

## Bruker- og styringsgrensesnitt

Desktop-GUI-et er det implementerte menneskelige brukergrensesnittet. Fra v0.1.2-a7 finnes også lokal CLI (`n5wf`) for headless kontroll og kjøring av eksisterende `.n5jobs`-jobblister. Workflow Manager er ikke arkitektonisk avhengig av GUI-et.

Jobber, jobblister, workflow-kjøring, kontrollpunkter, status og resultater skal håndteres gjennom samme underliggende jobb-/workflow-/executorlag fra flere innganger.

Gjeldende prinsipp:

```text
Desktop GUI --------+
CLI ----------------+--> Preflight / BatchRunner / JobRunner --> Executor --> Operations
framtidig API ------+
```

CLI-et bruker `JobPreflight`, `BatchRunner`, `JobRunner` og `LocalExecutor` uten at desktop-GUI-et er startet. Et framtidig nettverks-API, servergrensesnitt eller annen ekstern stimulus skal bygge videre på samme jobb- og kommandomodell, ikke etablere en parallell workflow-implementasjon.

CLI-et i v0.1.2-a7 dekker kontroll og kjøring av eksisterende jobblister. Grunnprinsippet er fortsatt at jobb-/workflowfunksjoner gradvis skal kunne opprettes, lastes, kjøres, fortsettes og følges uten aktivt GUI, men funksjoner som ikke er dokumentert i `CLI.md` skal ikke regnes som implementert CLI-funksjonalitet.

Den offentlige CLI-syntaksen, argumenter, flags og exit codes dokumenteres autoritativt i `CLI.md`. Generelle programkontrakter og framtidige API-/datautvekslingsgrenser dokumenteres i `INTERFACE.md`.

## Bevaringsprinsipp for Noark 5-kilden

Mottatt Noark 5-uttrekk betraktes som bevis. Analyse, validering og kontroll skal som hovedregel være read-only. Dersom fremtidige operasjoner lager konverterte eller avledede representasjoner, skal original og avledet objekt skilles tydelig og dokumenteres.

DIAS SIP/AIC er et separat pakkenivå. Pakking kan beskrive og supplere pakken uten å omskrive kildeuttrekket.

DIAS skal forstås som et pakkelag **over** uttrekksformatet. DIAS-elementer er ikke en del av Noark 5- eller SIARD-nivået i seg selv. For Noark 5 består DIAS-leveransen prinsipielt av selve uttrekket i TAR og en separat DIAS-metadata-XML på pakkenivået. Workflow Manager skal derfor ikke lete etter DIAS-metadatafilen inne i Noark 5-TAR-en. Samme nivåskille gjelder når innholdet er SIARD.

Noark 5-uttrekksformatet er i stor grad selvdokumenterende gjennom metadata, struktur, skjemaer, referanser og sjekksummer. AIP-/AIC-laget bør derfor ikke uten et konkret behov duplisere dokumentasjon som allerede finnes i uttrekket. Pakkelaget kan i stedet tilføre nødvendig proveniens, mottaks-/valideringsdokumentasjon, transformasjonshistorikk og forvaltningsinformasjon.

### TAR som direkte lesbar kilde

En eksisterende Noark 5-TAR skal kunne behandles som en direkte lesbar datakilde. Full uttrekking skal ikke være et automatisk krav.

Operasjoner bør kunne lese medlemsliste, XML, skjemaer, sjekksummer og annet relevant innhold direkte fra TAR når kontrollen tillater det. Enkeltfiler eller hele uttrekket trekkes ut når en konkret kontroll eller et eksternt verktøy krever fysisk filtilgang.

Dette er særlig viktig for store uttrekk, der unødvendig full uttrekking kan gi et svært stort ekstra behov for arbeidslagring.

### Valideringsmodell

Følgende nivåer er klare mål for den interne valideringsarkitekturen:

1. kontroll av forventede elementer og struktur
2. validering av XML mot tilhørende XSD-skjema
3. logisk validering mot Noark 5-regler og relevante opptellinger
4. validering av pekere/referanser fra XML til dokumentfiler

Følgende områder er aktuelle, men trenger videre gjennomgang før de låses som komplette funksjonskrav:

- full validering av dokumentfiler og dokumentformater
- PDF/A-validering av arkivversjoner
- valg og integrasjon av ekstern dokument-/PDF/A-validator, for eksempel veraPDF eller tilsvarende
- grenseflaten mot funksjonalitet som Arkade 5 tilbyr eller planlegger

### Normalisering og repakking

Original mottatt SIP/TAR skal som hovedregel kunne bevares urørt. Repakking er en eksplisitt transformasjon, ikke normal behandling.

Normalisering må likevel støttes når mottatt intern struktur ikke passer valgt bevarings-/arbeidsstrategi eller verktøykrav. Kjente eksempler er at Noark 5-roten ligger ett nivå for dypt, som `content/content/...`, eller at flere separate Noark 5-uttrekk ligger som undermapper i samme `content`.

Normalformen for denne arbeidsflyten er ett Noark 5-uttrekk med roten direkte i `content` på DIAS-nivået. Dette samsvarer også med strukturen som brukes ved Arkade 5-testing.

En repakking skal være sporbar og dokumentere mottatt kilde, hva som ble endret, relevante sjekksummer og produsert resultat. Dersom flere uttrekk splittes til separate SIP-er, skal koblingen til mottatt kilde dokumenteres.

## Workflow-logg, rapporter og PREMIS

Tre dokumentasjonslag skal holdes adskilt:

- **Workflow-/kjørelogg:** teknisk og operativ historikk.
- **Menneskelesbare rapporter:** kontroll-, analyse- og innholdsrapporter.
- **PREMIS-proveniens:** maskinlesbar proveniens for relevante bevarings-/valideringshendelser.

PREMIS-mekanismen ligger sentralt i `noark5_workflow/core/premis_logger.py`. Operasjoner produserer ikke PREMIS XML selv.

## Kjørebackend

### Nå

- `LocalExecutor`: kjører operasjonen lokalt og håndterer sentral PREMIS-registrering.
- `JobPreflight`: GUI-uavhengige kontroller og sikker normalisering før jobb-/batchkjøring.
- `JobRunner`: GUI-uavhengig kjøring av én jobb.
- `BatchRunner`: GUI-uavhengig sekvensiell kjøring av jobber/jobblister.

### Senere

- `RemoteExecutor`: sender jobber til én eller flere arbeidsflytservere/workere og skal bevare samme logging-/provenienskontrakt.

Operasjoner angir om de kan kjøres `local`, `server` eller `either`.

**Windows desktop er dagens testede hovedmiljø. Lokal headless CLI er også praktisk verifisert på Windows.** Plattformstatus, Windows Server/RDS, Linux, macOS, headless worker/server, web og mobile alternativer dokumenteres i `RUNTIME-ENVIRONMENTS.md`.

## Lokal persistens og ekstern dataintegrasjon

Workflow Manager er tenkt distribuert og trenger lokal persistent lagring for applikasjons- og arbeidsflytdata som må overleve mellom kjøringer og kunne brukes under behandling.

**SQLite er foretrukket kandidat** for denne lokale applikasjonsdatabasen, men konkret databaseskjema er ikke låst.

Den interne datamodellen skal være generisk og skal ikke modelleres etter ett bestemt lokalt regneark, CRM eller fagsystem. Eksterne datakilder skal kobles gjennom adaptere/grensesnitt som mapper mellom den eksterne modellen og Workflow Managers egne begreper.

```text
Excel / CSV / database / API / fagsystem
                 |
              adapter
                 |
                 v
      generisk intern datamodell
                 |
                 v
          lokal persistens
```

Lokal persistens kan blant annet holde jobbtilstand, behandlingsstatus, checkpoints, nødvendige eksterne identifikatorer, valideringsresultater, pakkeidentifikatorer og import-/eksportstatus.

En organisasjons eksisterende master-regneark kan brukes som test- eller migreringskilde, men skal ikke definere produktets datamodell.

Følgende er fortsatt åpne designspørsmål: endelig SQLite-skjema, obligatoriske generiske metadatafelt, autoritative kilder per felt, synkroniserings- og konfliktregler, offline-/online-modell, framtidig sentralt API og hvilke resultater/statusendringer som skal utveksles tilbake.

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

Se `CODE-MAP.md`, `CLI.md`, `SHARED-ROADMAP.md`, `JOBS-AND-BATCHES.md`, `JOBS-BATCH-FUTURE-DESIGN.md` og `RUNTIME-ENVIRONMENTS.md`.
