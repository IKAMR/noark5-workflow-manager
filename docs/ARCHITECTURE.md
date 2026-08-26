# Arkitektur

## Mål

Noark 5 Workflow Manager skal være et arbeidsflytramverk for analyse, validering og behandling av komplette Noark 5-uttrekk.

Arkitekturen skiller mellom:

1. **GUI** – valg av uttrekk og operasjoner, fremdrift og resultater.
2. **Kilde-/kontekstmodell** – beskriver Noark 5-uttrekket og hvilke kilder som finnes.
3. **Operasjoner** – avgrensede funksjoner som analyserer eller behandler uttrekket.
4. **Kjørebackend** – bestemmer hvor en operasjon faktisk kjøres.

Dette skillet gjør det mulig å beholde samme GUI og operasjonsmodell når serverkjøring senere innføres.

## Kjørebackend

### Nå

- `LocalExecutor`: kjører operasjonen lokalt på arbeidsstasjonen.

### Senere

- `RemoteExecutor`: sender jobber til én eller flere arbeidsflytservere.

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

Dokumentfilene i `dokumenter/` skal i første omgang ikke dybdevalideres. Aktuelle kontroller er primært:

- om dokumentreferansen finnes
- filstørrelse og størrelsesfordeling
- sammenheng mellom dokumentmetadata og fysisk fil

Tyngre dokumentanalyse kan senere implementeres som egne operasjoner.

## Analysemodell

Målet er å lese dyr metadata én gang og produsere en strukturert intern resultatmodell som flere rapporter og kontroller kan bruke.

Eksempel:

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

Dette unngår at `arkivstruktur.xml` må leses på nytt for hver rapport.

## Videre retning

Planlagte områder omfatter blant annet:

- U1 / N5.101
- U2 / N5.102
- full erstatning og utvidelse av eksisterende XPath-analyser
- analyser på tvers av Noark 5 XML-filer
- dokumentreferansekontroll
- rapporter i strukturerte formater
- DIAS/SIP/DIP-relaterte arbeidsflyter
- valgfri server-/arbeidsnodekjøring
