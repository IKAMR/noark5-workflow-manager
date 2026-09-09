# Logging, testresultater, vurdering og PREMIS

Dette dokumentet beskriver kontrakten mellom teknisk logging, jobb-/kjøringshistorikk,
rå testresultater, senere faglig vurdering, autoritative resultater og PREMIS-proveniens.

Målet er å bevare komplett sporbarhet uten at tekniske feil, brukerfeil eller feil i selve
testapparatet automatisk blir stående som påstander om arkivmaterialet.

## 1. Grunnprinsipp

Et registrert testresultat er en historisk observasjon fra en bestemt testdefinisjon og
kjøring. Det er **ikke automatisk en endelig faglig konklusjon** om uttrekket.

Systemet skal derfor skille mellom minst disse nivåene:

```text
teknisk hendelse / applikasjonslogg
              |
              v
jobb-/kjøringshistorikk
              |
              v
rått testresultat
              |
              v
vurdering / disposition
              |
              v
autoritativt resultatsett
              |
              +--> kontroll-/godkjenningsrapport
              +--> hovedrapport og vedlegg
              +--> senere database/API
              +--> PREMIS når eksplisitt provenienspolicy tilsier det
```

Dette skillet skal gjelde både native tester i Workflow Manager og senere adaptere mot
andre testverktøy.

## 2. Teknisk logg

Teknisk/applikasjonslogg kan være den rikeste og mest detaljerte historikken. Den kan
inneholde blant annet:

- ugyldig konfigurasjon
- feil mappevalg
- preflight-feil
- parser-/programfeil
- warnings
- retry og avbrutte forsøk
- diagnostisk informasjon

Slike hendelser skal ikke slettes bare fordi en senere kjøring lykkes. De er nyttige for
feilsøking og revisjon av selve arbeidsprosessen.

Teknisk logg er samtidig **ikke** en kilde som ukritisk skal kopieres til PREMIS eller
sluttrapporter.

## 3. Jobb- og kjøringshistorikk

Jobbhistorikken beskriver hva som faktisk ble forsøkt og utført i en bestemt jobb.
Den skal kunne skille mellom:

- konfigurasjon/preflight før en operasjon faktisk starter
- faktisk startet operasjon
- operasjon fullført med resultat
- operasjon feilet
- kontrollert ny kjøring eller retest

En ugyldig `source_extraction` som stoppes før relevant behandling av materialet er for
eksempel en reell teknisk/jobb-hendelse, men ikke nødvendigvis en hendelse på
arkivobjektet.

## 4. Rå testresultater skal bevares

Et rått testresultat skal representere hva en bestemt test faktisk rapporterte på et
gitt tidspunkt. Resultatet skal ikke omskrives i ettertid for å passe en senere
konklusjon.

For sporbarhet bør resultatet etter hvert kunne knyttes til blant annet:

- stabil test-ID
- versjon av testdefinisjonen
- kjørings-/resultat-ID
- tidspunkt
- hvilket uttrekk/objekt og scope som ble testet
- PASS/FAIL/annen teststatus
- strukturerte funn/avvik

Detaljert skjema for dette låses ikke i a17 steg 1.

## 5. Feil i testen må kunne underkjenne et tidligere funn

Et FAIL-resultat kan senere vise seg å være en falsk feil, for eksempel fordi XPath,
regelverkstolkning eller implementasjon i testen var feil. Da skal systemet støtte en
kjede som denne:

```text
Test N5-X v1
  -> FAIL
  -> testfeil identifisert
  -> resultat vurdert som feil i testapparatet
  -> testdefinisjon korrigert til v2
  -> retest
  -> PASS
  -> autoritativ konklusjon: ingen feil på dette punktet
```

Det første FAIL-resultatet skal fortsatt kunne finnes i teknisk/testhistorikk. Det skal
derimot ikke uten videre inngå som et gyldig avvik i endelig godkjenning, rapport eller
PREMIS.

Dette er et sentralt skille mellom **historisk sannhet om hva testen rapporterte** og
**faglig sannhet som senere er vurdert som gjeldende for uttrekket**.

## 6. Vurdering/disposition er et eget lag

Et rått resultat skal kunne få en senere vurdering uten at råresultatet endres.
Aktuelle begreper som foreløpig brukes i modellen er:

- `pending` – ikke ferdig vurdert
- `accepted` – resultatet godtas som gyldig grunnlag
- `rejected_test_defect` – resultatet underkjennes fordi testen/testdefinisjonen var feil
- `superseded` – resultatet er erstattet av nyere relevant resultat
- `requires_review` – krever manuell/faglig vurdering
- `confirmed_finding` – funnet er bekreftet som faglig gyldig

Navnene er interne a17-begreper og kan justeres før offentlig format låses. Det viktige
er selve skillet mellom råresultat og senere vurdering.

Vurderinger skal etter hvert være sporbare med begrunnelse, tidspunkt og aktør. En
manuell overstyring skal ikke være stille eller overskrive den opprinnelige historikken.

## 7. Autoritativt resultatsett

Sluttrapporter, godkjenningsgrunnlag og andre endelige fremstillinger skal bygges fra et
**autoritativt resultatsett**, ikke direkte fra alle historiske testkjøringer.

Det autoritative resultatsettet er den gjeldende faglige tolkningen etter at relevante
råresultater og vurderinger er tatt hensyn til.

Dette gjør det mulig å:

- bevare feilaktige tidligere testresultater for sporbarhet
- rette feil i testapparatet uten å forurense sluttrapporten
- markere reelle funn som bekreftet
- la enkelte funn stå til manuell vurdering
- erstatte eldre resultater med retest uten å slette historikken

## 8. PREMIS er en kontrollert projeksjon

PREMIS skal ikke brukes som database for all test- og saksbehandlingshistorikk.
Workflow Manager skal kunne bevare en rikere intern historikk enn den som uttrykkes i
PREMIS.

PREMIS-hendelser skal senere genereres gjennom eksplisitt provenienspolicy basert på
semantisk relevante hendelser og autoritative resultater.

Følgende skal derfor **ikke automatisk** bli PREMIS-hendelser om arkivobjektet:

- feil mappevalg som stoppes før behandling
- ugyldig konfigurasjon
- preflight-feil
- program-/GUI-feil
- et test-FAIL som senere underkjennes som feil i testapparatet

En faktisk utført bevarings-, validerings-, migrerings-, slettings- eller pakkingshendelse
kan være relevant for PREMIS, men avgjørelsen skal ligge i eksplisitte regler og ikke i
at logglinjen hadde status OK eller FEIL.

## 9. Rapporter og U1/U2-retningen

Noark 5-analysegrunnlaget og U1/U2-lignende rapportering skal følge samme prinsipp:

- test-/analysemotor produserer strukturerte råresultater
- vurderingslaget bestemmer hvilke resultater som er gjeldende
- rapportlaget presenterer autoritative resultater for hele uttrekket og per arkivdel
- historiske/underkjente resultater kan vises i revisjons-/teknisk sammenheng ved behov,
  men skal ikke blandes inn som aktive avvik

Dermed kan testapparatet forbedres over tid uten at tidligere testfeil blir stående som
feil ved selve uttrekket.

## 10. a17 steg 1 – avgrensning

Dette første steget gjør bare følgende:

1. dokumenterer kontrakten over
2. introduserer en liten GUI-uavhengig modell for klassifisering av råresultat og vurdering
3. legger til regresjonstester for kontrakten
4. endrer **ikke** eksisterende PREMIS XML-format
5. endrer **ikke** hvilke eksisterende runtime-hendelser som faktisk skrives til PREMIS
6. introduserer **ikke** automatisk faglig beslutningslogikk

Neste steg kan koble klassifiseringen til runtime og innføre eksplisitte regler for hvilke
hendelser som er PREMIS-kandidater og hvordan testresultater går fra rått til vurdert og
autoritativt resultat.

## a17 steg 2 – eksplisitt proveniensport

Før en kjørt operasjon kan sendes til PREMIS-laget innføres en separat
klassifisering av hendelsens rolle. Klassifiseringen er ikke det samme som
resultatvurderingen over:

- `technical_only`: teknisk/applikasjonsmessig hendelse; skal ikke til PREMIS.
- `job_history`: relevant for jobb-/kjøringshistorikken; skal ikke i seg selv til PREMIS.
- `provenance_candidate`: hendelsen kan vurderes av PREMIS-policyen.

`provenance_candidate` betyr uttrykkelig **kandidat**, ikke automatisk PREMIS.
Eksisterende `premis_should_record()` gjelder fortsatt som neste kontroll. Senere
regler kan i tillegg kreve faglig vurdering eller autoritativt resultat før en
validerings-/analysehendelse blir del av endelig proveniens.

Preflight skjer før operasjonen kjøres og skal ikke skape PREMIS-hendelse. En
feil mappe, ugyldig konfigurasjon eller annen preflight-feil kan derfor beholdes
i teknisk logg og relevant jobbhistorikk uten å beskrives som mislykket
bevaringsbehandling av arkivobjektet.

Steg 2 migrerer konservativt: eksisterende operasjoner som ennå ikke har fått
eksplisitt klassifisering beholder dagens PREMIS-adferd. Når en operasjon får en
eksplisitt klassifisering, brukes den nye porten. Ukjente eksplisitte verdier
avvises (fail closed). Dette lar oss klassifisere operasjonene én for én uten å
endre alle eksisterende arbeidsflyter samtidig.

## a17 steg 3 – append-only vurderingslogg

For å støtte feil i eget testapparat uten å omskrive historikken innføres en liten intern vurderingslogg (`ResultReviewLedger`). Den lagrer vurderingshendelser append-only som JSONL.

Prinsippene er:

- Rått testresultat endres ikke når vurderingen endres.
- En ny vurdering legges til som en ny hendelse.
- Siste vurdering per `result_id` brukes når et nåværende autoritativt resultatsett avledes.
- `rejected_test_defect` og `superseded` blir liggende i historikken, men bidrar ikke til det autoritative resultatsettet.
- `accepted` og `confirmed_finding` kan bidra til det autoritative resultatsettet.
- Vurderingsloggen er **ikke PREMIS**, og den skriver ikke til PREMIS automatisk.
- JSONL-formatet er foreløpig en intern a17-kontrakt (`schema_version: 1`) og skal ikke behandles som et offentlig, stabilt utvekslingsformat ennå.

Eksempel på falsk feil beholdes dermed som en sporbar kjede:

`rå FAIL → rejected_test_defect → korrigert test → nytt råresultat → accepted`

Den første FAIL-en slettes ikke, men den inngår heller ikke i gjeldende autoritative konklusjon om uttrekket.

## a17 steg 4 – stabile råresultater og `result_id`

Faktiske test- og analyseoperasjoner kan nå eksplisitt velge append-only lagring av råresultatet. Dette er fortsatt et internt Workflow Manager-lag og **ikke PREMIS**.

Første operasjoner som kobles til ordningen er:

- `validate_xml_schema`
- `analyse_noark5_core`

Hver faktisk kjøring får en ny unik `result_id`. En ny kjøring av samme test overskriver derfor ikke beviset på hva den tidligere kjøringen faktisk observerte. Det eksisterende menneske-/maskinlesbare resultatet i operasjonens normale resultatmappe beholdes som før; i tillegg lagres en append-only råresultatkonvolutt under:

```text
<work_operations>/wf/results/raw-results.jsonl
```

Det er bevisst ingen fallback til Source. Dersom `work_operations` ikke er definert, skal dette laget ikke skrive noe ved siden av kilden.

Råresultatet inneholder blant annet:

- `result_id`
- tidspunkt
- operasjon-ID
- test-/definisjons-ID
- definisjonsversjon
- PASS/FAIL slik operasjonen faktisk returnerte
- melding og strukturert `data`
- kildeidentifikasjon
- eventuell jobb-ID dersom den finnes i kjørekonteksten

Operasjonens vanlige `OperationResult.data` får i tillegg en `_result_ref` som peker på samme `result_id`, test-ID og råresultatlager. Dermed kan senere vurdering, rapportering og godkjenning referere eksplisitt til den konkrete kjøringen i stedet for bare til et filnavn som kan være overskrevet av en senere kjøring.

### Forholdet til falske FAIL

Dette steget gjør det mulig å bevare følgende kjede uten å forveksle observasjon og konklusjon:

```text
result_id A: test v1 -> FAIL
    -> vurdering: rejected_test_defect / superseded
result_id B: korrigert test v2 -> PASS
    -> vurdering: accepted
```

`result_id A` slettes eller omskrives ikke. Den kan fortsatt forklare utviklings- og kvalitetshistorikken, men vurderingslaget kan ekskludere den fra det autoritative resultatsettet. `result_id B` er en ny selvstendig observasjon.

### Konservativ migrering

Råresultatlagring er opt-in per operasjon med `raw_result_record = True`. Vi gjør derfor ikke alle eksisterende operasjonsresultater til testresultater automatisk. Nye test-/analyseoperasjoner bør ta stilling eksplisitt til om de produserer et vurderbart råresultat.

Dette steget endrer ikke PREMIS XML, og et lagret råresultat får ingen PREMIS-hendelse bare fordi det eksisterer.

## a17 steg 5 – praktisk, read-only innsyn i råresultater

Råresultatkjeden gjøres nå synlig i GUI uten å introdusere vurderingshandlinger eller
endre PREMIS. Hovedvinduet får en sekundær `Resultater`-handling for aktiv jobb.
Dialogen viser append-only råresultater fra jobbens eksplisitte område:

```text
<work_operations>/wf/results/raw-results.jsonl
```

Visningen viser tidspunkt, PASS/FAIL slik testen faktisk returnerte, test-/definisjons-ID,
`result_id` og operasjon. Den er med hensikt **read-only** i dette steget.

Viktige kontrakter:

- Resultatdialogen viser observasjoner, ikke endelig faglig vurdering.
- PASS/FAIL i dialogen skal derfor ikke forstås som autoritativ godkjenning eller avvik.
- Resultater filtreres til aktiv `JOB-xxx` når `job_id` finnes i råresultatet.
- Tidlige a17-resultater uten `job_id` kan bare vises via en konservativ fallback når
  `source_root` matcher aktiv jobbs konkrete uttrekksrot.
- Det finnes ingen fallback til Source dersom `work_operations` mangler.
- Dialogen skriver ikke til vurderingsloggen og skriver ikke PREMIS.
- Flere raske åpninger skal fokusere eksisterende dialog i stedet for å opprette flere.

Dette gir praktisk verifikasjon av kjeden `testkjøring -> result_id -> råresultatlager`
før vi senere introduserer eksplisitte brukerhandlinger for vurdering/disposition.
