# Grensesnitt og kontrakter

Dette dokumentet beskriver stabile programkontrakter og brukergrensesnittregler som andre deler av Noark 5 Workflow Manager skal kunne bygge på.

## Operasjoner

Operasjoner registreres i `OperationRegistry`, mottar en `OperationContext` og returnerer et `OperationResult`. GUI skal ikke omgå executorlaget for å kjøre operasjoner direkte.

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

Workflow-modellen eier rekkefølgen på valgte operasjoner. GUI-komponentene presenterer denne tilstanden, men skal ikke være eneste lagringssted for den.

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

## Knappestiler og handlingshierarki

Knappfarge skal uttrykke handlingens rolle konsekvent i hele applikasjonen.

- **Primær (blå):** hovedhandlingen som fullfører eller starter aktuell oppgave, for eksempel `Legg til i workflow`, `Kjør workflow`, `Start alle` eller `Lagre` i en bekreftelsesdialog.
- **Sekundær (mørk):** støttehandlinger som valg, import, åpning, redigering, oppdatering og navigasjon.
- **Stopp/fare:** egen tydelig stil brukes bare når handlingen stopper, sletter eller har en konsekvens som bør fremheves.
- En dialog skal normalt ha bare én visuelt primær handling.
- Farge skal ikke være eneste signal for fare eller status; knappetekst og kontekst skal også være tydelig.

## Operasjonsmodenhet

Operasjoner har eksplisitt modenhetsnivå definert i `config/operations.json`.

- `Alpha`: eksperimentell og kan endres betydelig.
- `Beta`: funksjonell, men fortsatt under utvikling og testing.
- `Stabil`: klar for normal bruk.

Innstillingen for operasjonssynlighet bruker `Alle (inkl. Alpha)`, `Beta og stabile` og `Kun stabile`. Internt kan verdiene `0`, `1` og `2` beholdes for bakoverkompatibilitet.

Workflow-listen bruker kompakt modenhetsmerking på én rad:

- `(S)` = Stabil
- `(B)` = Beta
- `(A)` = Alpha

## Huskede mapper

Dialoger som åpner eller lagrer filer og mapper skal huske siste relevante lokasjon med egne, tydelig navngitte innstillinger.

- `last_noark_source_dir`
- `last_dias_output_dir`
- `last_mets_import_dir`
- `last_dias_add_file_dir`
- `last_dias_add_folder_dir`
- `last_setup_dir`
- `last_job_list_dir`
- `last_job_list_file`

Ved import av setup skal `last_setup_dir` settes til mappen setup-filen faktisk ble lest fra på denne maskinen.

## Standardmapper og sist brukte mapper

Konfigurerte standardmapper og sist brukte dialogmapper er forskjellige begreper.

- `setup_dir` bestemmer standardplassering for setup.
- `job_list_dir` bestemmer standardplassering for jobblister.
- `run_log_dir` bestemmer standardplassering for overordnede kjørelogger.
- `last_setup_dir` og `last_job_list_dir` beskriver hvor brukeren sist faktisk åpnet eller lagret noe.

Tom eksplisitt standardverdi eller `Bruk standard` betyr fallback under `temp_dir`:

- kjørelogg: `<temp_dir>/logs/runs`
- setup: `<temp_dir>/setup`
- jobblister: `<temp_dir>/joblists`

## Planlagte generiske kontrakter

### Transfer/verify

En transfer-operasjon skal minst beskrive eksplisitt kilde, destinasjon, lagringsrolle, verifikasjonsmetode og resultat. Kilden skal ikke endres som sideeffekt av verifikasjon.

### External validator adapter

Et eksternt verktøy som Arkade 5 CLI skal kapsles som en normal operasjon og returnere `OperationResult` med exit-status, rapport-/loggreferanser og normaliserte funn der dette er tilgjengelig.

### Batch/recursive controller

Batchlaget oppdager og prequalifier kandidater, men kjører den faktiske jobben gjennom ordinær workflow/executor. Dermed finnes ikke to separate implementasjoner av samme validering.
