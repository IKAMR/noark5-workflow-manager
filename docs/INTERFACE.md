# Grensesnitt og kontrakter

Dette dokumentet beskriver stabile grensesnitt som andre deler av Noark 5 Workflow Manager skal kunne bygge på.

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

`DiasPackageOperation` er i v0.1.0 første konkrete Noark-operasjon som deklarerer en workflow-PREMIS-hendelse: `Creation` / `DIAS SIP/AIC-pakking`. Dette er separat fra package-level PREMIS/METS som DIAS-pakkingen allerede genererer internt.

### Utdatakontrakt for PREMIS

`BaseOperation.premis_output_dir(result, ctx)` returnerer eksplisitt målmappe for sentral workflow-PREMIS, eller `None` dersom ingen målmappe er valgt. Executor skal aldri falle tilbake til kildeområdet.

`DiasPackageOperation` returnerer den valgte DIAS-utdatamappen (foreldremappen til generert `aic_path`) som PREMIS-mål. Dermed skrives `<uttrekksnavn>_premis.xml` i samme eksplisitte utdataområde som DIAS-resultatet, ikke ved siden av Noark 5-kilden.

## Planlagte generiske kontrakter

### Transfer/verify

En transfer-operasjon skal minst beskrive eksplisitt kilde, destinasjon, lagringsrolle, verifikasjonsmetode og resultat. Kilden skal ikke endres som sideeffekt av verifikasjon.

### External validator adapter

Et eksternt verktøy som Arkade 5 CLI skal kapsles som en normal operasjon og returnere `OperationResult` med exit-status, rapport-/loggreferanser og normaliserte funn der dette er tilgjengelig.

### Batch/recursive controller

Batchlaget oppdager og prequalifier kandidater, men kjører den faktiske jobben gjennom ordinær workflow/executor. Dermed finnes ikke to separate implementasjoner av samme validering.
