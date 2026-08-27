# Arkitektur

## Mål

Noark 5 Workflow Manager skal være et arbeidsflytramverk for analyse, validering og behandling av komplette Noark 5-uttrekk.

Arkitekturen skiller mellom:

1. **GUI** – valg av uttrekk og operasjoner, fremdrift og resultater.
2. **Kilde-/kontekstmodell** – beskriver Noark 5-uttrekket og hvilke kilder som finnes.
3. **Operasjoner** – avgrensede funksjoner som analyserer eller behandler uttrekket.
4. **Kjørebackend** – bestemmer hvor en operasjon faktisk kjøres.
5. **Logging/proveniens** – vanlig workflow-logg for alle steg og sentral PREMIS-proveniens for relevante hendelser.

Dette skillet gjør det mulig å beholde samme GUI og operasjonsmodell når serverkjøring senere innføres.

## Bevaringsprinsipp for Noark 5-kilden

Mottatt Noark 5-uttrekk betraktes som bevis. Analyse, validering og kontroll skal som hovedregel være read-only. Dersom fremtidige operasjoner lager konverterte eller avledede representasjoner, skal original og avledet objekt skilles tydelig og dokumenteres.

DIAS SIP/AIC er et separat pakkenivå. Pakking kan beskrive og supplere pakken uten å omskrive kildeuttrekket.

## Workflow-logg, rapporter og PREMIS

Tre dokumentasjonslag skal holdes adskilt:

- **Workflow-/kjørelogg:** teknisk og operativ historikk. Alle operasjoner/tester registreres her.
- **Menneskelesbare rapporter:** kontroll-, analyse- og innholdsrapporter for saksbehandling/depotarbeid.
- **PREMIS-proveniens:** maskinlesbar proveniens for relevante bevarings-/valideringshendelser.

PREMIS-mekanismen ligger sentralt i `noark5_workflow/core/premis_logger.py`. Operasjoner produserer ikke PREMIS XML selv; de deklarerer metadata/hook-metoder som executor-/workflowlaget bruker. Dette følger samme generiske arkitektur som SIARD Workflow Manager.

I a10 oppretter `LocalExecutor`/gjenbruker én logger per `OperationContext`, registrerer aktuelle hendelser og skriver en samlet `<uttrekksnavn>_premis.xml` utenfor selve kildeuttrekket. Filen oppdateres etter hver registrerte hendelse slik at proveniens ikke tapes om et senere steg feiler.

## Kjørebackend

### Nå

- `LocalExecutor`: kjører operasjonen lokalt på arbeidsstasjonen og håndterer sentral PREMIS-registrering.

### Senere

- `RemoteExecutor`: sender jobber til én eller flere arbeidsflytservere. Remote-kjøring må bevare samme logging-/provenienskontrakt.

Operasjoner angir om de kan kjøres `local`, `server` eller `either`.

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

- `arkivstruktur.xml` – hovedmengden metadata og den viktigste ressursmessige XML-filen
- `arkivuttrekk.xml`
- `loependeJournal.xml`
- `offentligJournal.xml`
- `endringslogg.xml`
- virksomhetsspesifikke metadata
- XSD-skjemaer
- `dokumenter/` – dokumentfilene

En viktig gevinst sammenlignet med enkeltstående XPath-kjøringer er at operasjoner senere kan analysere og sammenligne flere XML-kilder i samme uttrekk.

## Ressurshåndtering

`arkivstruktur.xml` kan være stor. Den fremtidige analysemotoren bør derfor bruke strømmet XML-lesing og samle kompakte analyseresultater uten å laste hele dokumentet i minnet.

Dokumentfilene i `dokumenter/` skal i første omgang ikke dybdevalideres. Aktuelle kontroller er primært om dokumentreferansen finnes, filstørrelse/størrelsesfordeling og sammenheng mellom dokumentmetadata og fysisk fil.

## Analysemodell

Målet er å lese dyr metadata én gang og produsere en strukturert intern resultatmodell som flere rapporter og kontroller kan bruke.

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

## Videre retning

Planlagte områder omfatter blant annet U1/N5.101, U2/N5.102, full erstatning/utvidelse av XPath-analyser, analyser på tvers av XML-filer, dokumentreferansekontroll, rapporter, DIAS/SIP/DIP-relaterte arbeidsflyter og valgfri server-/arbeidsnodekjøring.

## Arbeidsområde, AIP-finalisering og AIC

Arbeidsflyten skal skille tydelig mellom tre områder:

1. **Kilde** – mottatt Noark 5-uttrekk. Read-only evidens.
2. **Arbeidsområde** – depotets tester, analysefiler, debug, rapporter, logger og mellomresultater. Området kan være omfattende og inneholde materiale som ikke skal langtidsbevares.
3. **AIP-finalisering / AIC-utdata** – eksplisitt kuratert innhold som skal bevares. Bare valgte relevante resultater fra arbeidsområdet tas med sammen med bevaringsobjektet.

SIP betegner innsendingspakken. Etter mottak/forvaltning og når innholdet inngår i arkivbevaringen, behandles den bevarte pakken som AIP; en AIC kan inneholde én eller flere AIP-er avhengig av depotmodellen. Programmet skal derfor ikke bruke «SIP» som generell betegnelse på alt innhold inne i en ferdig AIC.

### Finaliseringsprinsipp

Finalisering bør senere være et eksplisitt workflow-steg som bygger en manifestert/visbar kandidatliste for AIP: kildeinnhold + valgte rapporter/proveniens/resultater. Brukeren skal kunne se hva som inkluderes og utelate ren debug, duplikater og midlertidige filer før AIC produseres.

Workflow-PREMIS og andre genererte sidefiler skal skrives i eksplisitt arbeids-/utdataområde. Ingen generert fil skal plasseres i kildeområdet som fallback.
