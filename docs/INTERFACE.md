# Grensesnitt

## Knappestiler og handlingshierarki

Knappfarge skal uttrykke handlingens rolle konsekvent i hele applikasjonen.

- **Primær (blå):** hovedhandlingen som fullfører eller starter aktuell oppgave, for eksempel `Legg til i workflow`, `Kjør workflow`, `Start alle` eller `Lagre` i en bekreftelsesdialog.
- **Sekundær (mørk):** støttehandlinger som valg, import, åpning, redigering, oppdatering og navigasjon. Eksempler er `Velg mappe…`, `Les inn fra METS-fil…`, `Åpne`, `Ny jobb`, `Avbryt`, `Legg til fil`, `Legg til mappe` og `Opprett mappe`.
- **Stopp/fare:** egen tydelig stil brukes bare når handlingen stopper, sletter eller har en konsekvens som bør fremheves.
- En dialog skal normalt ha bare én visuelt primær handling.
- Farge skal ikke være eneste signal for fare eller status; knappetekst og kontekst skal også være tydelig.

DIAS-dialogen bruker derfor mørk stil på både `Velg mappe…` og `Les inn fra METS-fil…`, mens `Legg til i workflow` er primær.

## Operasjonsmodenhet

Operasjoner har eksplisitt modenhetsnivå definert i `config/operations.json`.

- `Alpha`: eksperimentell og kan endres betydelig.
- `Beta`: funksjonell, men fortsatt under utvikling og testing.
- `Stabil`: klar for normal bruk.

Modenhetsnivå skal vises når en operasjon velges i operasjonspaletten. Farge skal ikke være eneste signal; teksten `Alpha`, `Beta` eller `Stabil` skal være synlig.

Innstillingen for operasjonssynlighet bruker brukerforståelige valg: `Alle (inkl. Alpha)`, `Beta og stabile` og `Kun stabile`. Internt kan verdiene `0`, `1` og `2` beholdes for bakoverkompatibilitet.

## Kompakt modenhetsmerking

Workflow-listen skal bruke én rad per operasjon. Modenhet vises som et kort prefiks:

- `(S)` = Stabil
- `(B)` = Beta
- `(A)` = Alpha

Eksempel: `1. (S) DIAS-pakking (SIP/AIC)`.

I operasjonspaletten og Innstillinger brukes de fulle tekstverdiene.

## Huskede mapper

Dialoger som åpner eller lagrer filer og mapper skal huske siste relevante lokasjon med egne, tydelig navngitte innstillinger. Disse er brukerkomfort og skal ikke blandes med jobbdata.

Gjeldende standardnøkler:

- `last_noark_source_dir` – sist valgte Noark-kildemappe
- `last_dias_output_dir` – sist valgte DIAS-utdatamappe
- `last_mets_import_dir` – sist brukte mappe for METS-import
- `last_dias_add_file_dir` – sist brukte mappe ved «Legg til fil»
- `last_dias_add_folder_dir` – sist brukte mappe ved «Legg til mappe»
- `last_setup_dir` – sist brukte mappe for eksport/import av setup
- `last_job_list_dir` – sist brukte mappe for åpning/lagring av jobblister
- `last_job_list_file` – sist brukte jobblistefil, brukt for automatisk gjenåpning

Ved import av setup skal `last_setup_dir` settes til mappen setup-filen faktisk ble lest fra på denne maskinen, slik at en sti fra en annen maskin ikke overstyrer den lokale dialoglokasjonen.

## Standardmapper og sist brukte mapper

Konfigurerte standardmapper og sist brukte dialogmapper er forskjellige begreper.

- `setup_dir` bestemmer standardplassering for setup.
- `job_list_dir` bestemmer standardplassering for jobblister.
- `run_log_dir` bestemmer standardplassering for overordnede kjørelogger.
- `last_setup_dir` og `last_job_list_dir` beskriver hvor brukeren sist faktisk åpnet eller lagret noe.

Tom eksplisitt standardverdi eller `Bruk standard` betyr fallback til undermappen under `temp_dir`:

- kjørelogg: `<temp_dir>/logs/runs`
- setup: `<temp_dir>/setup`
- jobblister: `<temp_dir>/joblists`
