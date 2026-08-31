# Grensesnitt og kontrakter

Dette dokumentet beskriver stabile programkontrakter og grensesnitt/datautveksling som andre deler av Noark 5 Workflow Manager eller eksterne systemer skal kunne bygge på.

Arkitektur og ansvarsdeling beskrives i `ARCHITECTURE.md`. GUI-konvensjoner og generell innstillingsadferd dokumenteres i `DEVELOPMENT.md` og relevante spesialdokumenter.

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

Workflow-modellen eier rekkefølgen på valgte operasjoner. GUI-komponentene presenterer denne tilstanden, men skal ikke være eneste lagringssted for den. Samme prinsipp gjelder planlagte CLI-/API-klienter.

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

Workflow Manager skal ha et maskinrettet styringsgrensesnitt ved siden av desktop-GUI-et. Første naturlige eksponering er en CLI; senere kan samme underliggende kontrakt eksponeres gjennom nettverks-API, tjeneste eller annen ekstern stimulus.

Grensesnittet skal bygges over jobb-/workflowlaget og skal kunne utvikles mot operasjoner som:

- opprette eller importere en jobb
- åpne/importere en jobbliste
- starte én jobb
- starte en jobbliste/batch
- fortsette en jobb fra kontrollpunkt
- stoppe/avbryte der executor støtter det
- hente jobbstatus, fremdrift og resultat-/loggreferanser

CLI og framtidig API skal ikke ha egen workflow-implementasjon. De skal bruke samme underliggende jobb-/workflowtjenester som GUI-et.

Endelig kommandomodell, CLI-syntaks, serialiseringsformat, exit-koder, autentisering og nettverks-API er åpne designspørsmål.

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

Batchlaget oppdager og prequalifier kandidater, men kjører den faktiske jobben gjennom ordinær workflow/executor. Dermed finnes ikke to separate implementasjoner av samme validering.
