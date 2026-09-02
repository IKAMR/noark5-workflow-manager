# Grensesnitt og kontrakter

Dette dokumentet beskriver stabile programkontrakter og grensesnitt/datautveksling som andre deler av Noark 5 Workflow Manager eller eksterne systemer skal kunne bygge på.

Arkitektur og ansvarsdeling beskrives i `ARCHITECTURE.md`. Den offentlige `n5wf`-kommando-/brukerkontrakten beskrives autoritativt i `CLI.md`. GUI-konvensjoner og generell innstillingsadferd dokumenteres i `DEVELOPMENT.md` og relevante spesialdokumenter.

## Operasjoner

Operasjoner registreres i `OperationRegistry`, mottar en `OperationContext` og returnerer et `OperationResult`. GUI eller andre klientgrensesnitt skal ikke omgå executorlaget for å kjøre operasjoner direkte.

### PREMIS-kontrakt for operasjoner

En operasjon kan deklarere:

```python
premis_record = True
premis_event_type = "Creation"
premis_event_label = "beskrivende tekst"
```

og kan overstyre:

```python
premis_should_record(result, ctx) -> bool
premis_detail(result, ctx) -> str
```

Operasjonen skal **ikke** skrive workflow-PREMIS XML selv. `LocalExecutor` bruker den sentrale `PremisProvenanceLogger`.

`premis_event_type` må være en gyldig DIAS_PREMIS v2.0-verdi: `Creation`, `Ingestion`, `Migration`, `Adjustment`, `Deletion` eller `Disposal`. Ugyldig verdi faller tilbake til `Adjustment`, mens fri beskrivende tekst hører hjemme i `premis_event_label`/`eventDetail`.

## OperationContext

`OperationContext` inneholder kilde, settings, callbacks samt delte `metadata` og `results`. Den sentrale PREMIS-loggeren lagres i `ctx.metadata["premis_logger"]`, og operasjonsresultatdata registreres i `ctx.results` av executorlaget.

## Workflow

Workflow-modellen eier rekkefølgen på valgte operasjoner. GUI-komponentene presenterer denne tilstanden, men skal ikke være eneste lagringssted for den. Samme prinsipp gjelder den implementerte CLI-en og senere API-klienter.

## LocalExecutor

`LocalExecutor.execute()` er den sentrale lokale kjøregrensen. Den:

1. validerer `can_run()`
2. kjører operasjonen
3. lagrer resultatdata i konteksten
4. registrerer PREMIS-hendelse når operasjonen/hookene krever det
5. skriver oppdatert proveniensfil

Fremtidig `RemoteExecutor` må opprettholde tilsvarende semantikk på serversiden.

## DIAS-pakking

DIAS-dialogen produserer parametere til DIAS-operasjonen. Valgt Noark 5-uttrekk er kildeinnhold. Manuelt lagt til filer og mapper er tilleggsinnhold i den genererte pakken og skal ikke skrives tilbake til kildemappen på disk.

`DiasPackageOperation` deklarerer workflow-PREMIS-hendelsen `Creation` / `DIAS SIP/AIC-pakking`. Dette er separat fra package-level PREMIS/METS som DIAS-pakkingen genererer internt.

### Utdatakontrakt for PREMIS

`BaseOperation.premis_output_dir(result, ctx)` returnerer eksplisitt målmappe for sentral workflow-PREMIS, eller `None` dersom ingen målmappe er valgt. Executor skal aldri falle tilbake til kildeområdet.

`DiasPackageOperation` returnerer den valgte DIAS-utdatamappen som PREMIS-mål. Dermed skrives `<uttrekksnavn>_premis.xml` i eksplisitt utdataområde, ikke ved siden av Noark 5-kilden.

## Programmatisk styringsgrensesnitt

Workflow Manager har fra v0.1.2-a7 et lokalt maskinrettet CLI-grensesnitt (`n5wf`) ved siden av desktop-GUI-et. CLI-et er første implementerte eksponering av det delte jobb-/workflowlaget. Senere kan samme underliggende kontrakt eksponeres gjennom nettverks-API, tjeneste eller annen ekstern stimulus.

CLI-et ble først implementert i v0.1.2-a7 for kontroll og kjøring av eksisterende `.n5jobs`-jobblister, og er senere utvidet innen samme delte jobb-/workflowmodell. Kommandoer, argumenter, flags og exit codes som faktisk er støttet, dokumenteres i `CLI.md` og skal ikke dupliseres her.

Det videre styringsgrensesnittet skal kunne utvikles mot operasjoner som:

- opprette eller importere en jobb
- åpne/importere en jobbliste
- starte én jobb
- starte en jobbliste/batch
- fortsette en jobb fra kontrollpunkt
- stoppe/avbryte der executor støtter det
- hente jobbstatus, fremdrift og resultat-/loggreferanser

Listen over beskriver retning; enkelte handlinger er allerede implementert og låst gjennom `CLI.md`.

Fra v0.1.2-a9 kan status leses for en jobbliste eller én jobb innen en eksplisitt angitt `.n5jobs`-fil. Dagens `JOB-001`-lignende jobb-ID er ikke global; ulike jobblister kan inneholde samme jobb-ID. Inntil en eventuell workspace/database/global identitetsmodell finnes, skal CLI-design derfor ikke anta at en løs jobb-ID alene kan identifisere en jobb sikkert.

Fra v0.1.2-a10 kan én valgt jobb kjøres innen en eksplisitt angitt `.n5jobs`-fil. Adresseringen er fortsatt kombinasjonen jobbliste + jobb-ID; dette innfører ikke global jobbidentitet.

Fra v0.1.2-a11 kan én jobb som står ved kontrollpunkt fortsettes eksplisitt med samme adresseringsmodell. `JobRunner.continue_job()` er den delte Core-kontrakten for denne styringshandlingen og brukes av både CLI og GUI. Den validerer at jobben faktisk står `Venter ved kontrollpunkt`, at execution cursor peker på en gjenværende operasjon, og at ventetilstanden er forankret i et reelt kontrollpunkt før ordinær `JobRunner.run()` gjenbrukes.

### Mulig framtidig CLI-syntaks

Som arbeidshypotese kan noen av de fortsatt ikke implementerte operasjonene ovenfor senere eksponeres med kommandoer som:

```text
n5wf job run <job-id>
n5wf job status <job-id>
n5wf job stop <job-id>

n5wf jobs status <file.n5jobs>
```

De løse `n5wf job ... <job-id>`-eksemplene forutsetter en framtidig identitets-/workspace-modell som gjør jobb-ID-en entydig.

Fortsettelse med dagens identitetsmodell er implementert og dokumentert autoritativt i `CLI.md`:

```text
n5wf jobs continue <file.n5jobs> --job <job-id>
```

Mulige framtidige options kan blant annet være:

```text
--job-id
--from
--until
--force
--output
```

Navn, syntaks og semantikk for de framtidige eksemplene over er **ikke låst** og betyr ikke at funksjonene er implementert. Når en offentlig kommando eller option faktisk implementeres og låses, dokumenteres den autoritativt i `CLI.md`.

CLI og framtidig API skal ikke ha egen workflow-implementasjon. De skal bruke samme underliggende jobb-/workflowtjenester som GUI-et. I dagens lokale kjørevei brukes `JobPreflight`, `BatchRunner`, `JobRunner` og `LocalExecutor`.

Implementert CLI-syntaks og exit codes er låst og dokumentert i `CLI.md`. Serialiseringsformat utover dagens `.n5jobs`, autentisering, nettverks-API og ytterligere kommandoer er fortsatt åpne designområder.

## Eksterne datakilder

Workflow Manager skal kunne utveksle data med eksterne kilder gjennom adaptere fremfor å bindes til ett bestemt regneark, database- eller CRM-skjema.

Prinsipiell grense:

```text
Ekstern kilde <-> adapter <-> generisk Workflow Manager-modell
```

Ekstern identitet og intern Workflow Manager-jobbidentitet skal kunne holdes adskilt. Den konkrete adapterkontrakten, obligatoriske metadatafelt, synkronisering og framtidig sentralt API er ikke ferdig spesifisert.

## Planlagte generiske kontrakter

### Transfer/verify

En transfer-operasjon skal minst beskrive eksplisitt kilde, destinasjon, lagringsrolle, verifikasjonsmetode og resultat. Kilden skal ikke endres som sideeffekt av verifikasjon.

### External validator adapter

Et eksternt verktøy som Arkade 5 CLI skal kapsles som en normal operasjon og returnere `OperationResult` med exit-status, rapport-/loggreferanser og normaliserte funn der dette er tilgjengelig.

Samme adapterprinsipp kan brukes for framtidige dokument-/PDF/A-validatorer. Valg av slikt verktøy er ikke låst.

### Batch/recursive controller

Sekvensiell batchkjøring av eksisterende jobblister er implementert gjennom `BatchRunner`. Framtidig recursive discovery skal oppdage og prequalifisere kandidater, men kjøre den faktiske jobben gjennom ordinær jobb-/workflow-/executor-kjede. Dermed finnes ikke to separate implementasjoner av samme validering.
