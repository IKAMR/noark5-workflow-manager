# Utviklingsregler

Før analyse eller endring av kode i dette repositoriet:

1. Les `docs/DEVELOPMENT.md`.
2. Les `docs/ARCHITECTURE.md` der den er relevant.
3. Les `docs/INTERFACE.md` ved endringer i grensesnitt eller kontrakter.
4. Les `docs/CLI.md` ved endringer i offentlig CLI-syntaks, argumenter, flags, exit codes eller CLI-brukeradferd.
5. Les `docs/DEFINITIONS.md` ved endringer som berører begreper og lagdeling.
6. Les `docs/TESTING.md` ved endringer som krever ny eller endret validering.
7. Les `docs/CODE-MAP.md` for å finne riktig lag og dataflyt.
8. Les `docs/RUNTIME-ENVIRONMENTS.md` ved endringer i installasjon, oppstart, filstier, brukerdata, eksterne programmer, packaging, server/worker eller plattformstøtte.
9. Les `docs/SHARED-DEVELOPMENT.md` og `docs/SHARED-ROADMAP.md` før generiske workflow-/depotendringer som også kan være relevante for SIARD Workflow Manager.
10. Behandle dokumentert arkitektur som målbildet. Kontroller samtidig den faktiske koden før endringer gjøres.

## Endringsprinsipp

- Bevar fungerende funksjonalitet og gjør den minste nødvendige endringen.
- Ikke erstatt et etablert GUI-panel i sin helhet bare for å legge til en kontroll eller funksjon.
- Noark 5-uttrekket og DIAS SIP/AIC er separate lag.
- Mottatt Noark 5-uttrekk behandles som bevaringsbevis og skal som hovedregel analyseres, valideres og dokumenteres uten å endres.
- Nye funksjoner skal ha automatiserte tester når det er praktisk mulig.
- Før commit av en alpha: kjør `test.bat`, deretter praktisk test via relevante implementerte grensesnitt. GUI-endringer testes via `start.bat`; CLI-endringer testes også med relevante `n5wf`-kommandoer.

Nye tanker eller framtidsretninger skal normalt legges til som avgrensede arkitektur-/designpresiseringer. Eksisterende dokumentasjon skal ikke omskrives bredt dersom den fortsatt er korrekt.

## GUI-konvensjoner

Følgende regler er flyttet hit fra `INTERFACE.md` fordi de beskriver GUI-/utviklingskonvensjoner, ikke datautvekslingsgrensesnitt.

### Knappestiler og handlingshierarki

Knappfarge skal uttrykke handlingens rolle konsekvent i hele applikasjonen.

- **Primær (blå):** hovedhandlingen som fullfører eller starter aktuell oppgave, for eksempel `Legg til i workflow`, `Kjør workflow`, `Start alle` eller `Lagre` i en bekreftelsesdialog.
- **Sekundær (mørk):** støttehandlinger som valg, import, åpning, redigering, oppdatering og navigasjon.
- **Stopp/fare:** egen tydelig stil brukes bare når handlingen stopper, sletter eller har en konsekvens som bør fremheves.
- En dialog skal normalt ha bare én visuelt primær handling.
- Farge skal ikke være eneste signal for fare eller status; knappetekst og kontekst skal også være tydelig.

### Operasjonsmodenhet

Operasjoner har eksplisitt modenhetsnivå definert i `config/operations.json`.

- `Alpha`: eksperimentell og kan endres betydelig.
- `Beta`: funksjonell, men fortsatt under utvikling og testing.
- `Stabil`: klar for normal bruk.

Innstillingen for operasjonssynlighet bruker `Alle (inkl. Alpha)`, `Beta og stabile` og `Kun stabile`. Internt kan verdiene `0`, `1` og `2` beholdes for bakoverkompatibilitet.

Workflow-listen bruker kompakt modenhetsmerking på én rad:

- `(S)` = Stabil
- `(B)` = Beta
- `(A)` = Alpha

### Jobbliste

- Rekkefølgen på jobbene i `.n5jobs` er den sekvensielle batchrekkefølgen. GUI-et kan endre denne rekkefølgen med Opp/Ned.
- Sletting av en jobb fjerner bare jobbposten fra jobblista. Kilde, utdata og tidligere resultatmapper på disk skal ikke slettes som sideeffekt.
- Flytting og sletting av jobber er deaktivert mens batch kjører.
- Når en tidligere kjørt jobb redigeres slik at gjeldende konfigurasjon må kjøres på nytt, kan den interne statusen være `Klar`. GUI-et skal samtidig synliggjøre dette som `Klar – endret etter kjøring`. Kravet om eksplisitt rerun-godkjenning beholdes.

## Innstillinger og mappeadferd

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

Konfigurerte standardmapper og sist brukte dialogmapper er forskjellige begreper.

- `setup_dir` bestemmer standardplassering for setup.
- `job_list_dir` bestemmer standardplassering for jobblister.
- `run_log_dir` bestemmer standardplassering for overordnede kjørelogger.
- `last_setup_dir` og `last_job_list_dir` beskriver hvor brukeren sist faktisk åpnet eller lagret noe.

Tom eksplisitt standardverdi eller `Bruk standard` betyr fallback under `temp_dir`:

- kjørelogg: `<temp_dir>/logs/runs`
- setup: `<temp_dir>/setup`
- jobblister: `<temp_dir>/joblists`

Se også `APP-WORKSPACE-AND-RUN-LOGS.md`.

## CLI-konvensjoner

- Offentlige CLI-kommandoer, subcommands, argumenter og flags skal være korte, presise og på engelsk.
- `docs/CLI.md` er autoritativ brukerreferanse for implementert `n5wf`-syntaks og exit codes.
- `noark5_workflow/cli.py` skal være et klient-/adapterlag over delte tjenester/core, ikke en parallell workflow-implementasjon.
- Jobb-, preflight- og batchsemantikk som både GUI og CLI trenger skal ligge i delte komponenter som `JobPreflight`, `JobRunner` og `BatchRunner`.
- Menneskelesbar terminaltekst kan være lokalisert selv om kommandosyntaksen er stabil og engelsk.

## Installasjonskonvensjoner

- Brukeren velger `GUI + CLI`, `GUI` eller `CLI`; Core er en intern felleskomponent og ikke et separat menyvalg.
- Installering av GUI eller CLI skal bevare den andre allerede installerte profilen.
- Core regnes som aktiv så lenge minst én av GUI/CLI er installert.
- Installert profilstatus lagres per bruker i `install-state.json` under Workflow Managers `%LOCALAPPDATA%`-område.
- Installasjonsstatus er teknisk metadata og skal ikke blandes med jobb-/workflowdata.
- Deinstallasjon skal kreve eksplisitt `Ja` før endringer utføres.
- Deinstallasjon av ett grensesnitt skal beholde Core dersom det andre fortsatt er installert.
- Generelle Python-avhengigheter (`lxml`, `psutil`, `customtkinter` osv.) skal ikke avinstalleres automatisk fordi de kan være delt med andre programmer.
- Installer/deinstaller skal ikke slette repository, jobblister, logger, config eller andre brukerdata.
- `install.bat`, `deinstall.bat`, `requirements*.txt` og `pyproject.toml` beholdes i repository-roten.

## Kjøremiljø og portabilitet

- Windows desktop er dagens testede hovedbaseline; lokal `n5wf` CLI er også praktisk verifisert på Windows.
- Ikke dokumenter Linux, macOS, server eller andre miljøer som støttet før installasjon, oppstart og relevant praktisk test er etablert.
- Ikke legg ny domenelogikk i `.bat`, `.sh` eller packaging.
- Unngå hardkodede Windows-stier i core/operations.
- Bruk plattformuavhengige Python-API-er og `pathlib` når mulig.
- Runtime-state og brukerinnstillinger skal på sikt ligge i egnet per-user application-data-område, ikke være avhengig av repository/installasjonsmappen.
- Eksterne programmer skal kapsles i adaptere med konfigurerbar executable/path.
- Core/operations skal ikke avhenge av GUI.
- Jobb- og workflowfunksjoner som skal brukes fra GUI, CLI og senere API skal ligge i delte tjenester/core og ikke bare i GUI- eller CLI-handlere.
- Lokal og framtidig remote kjøring skal bevare samme operations/executor-kontrakt.

Se `docs/RUNTIME-ENVIRONMENTS.md`.

## Workflow logging og PREMIS-proveniens

- **Alle operasjoner/tester** skal fremgå av vanlig workflow-/kjørelogg.
- Relevante bevarings-, validerings-, migrerings-, slettings- og pakkingshendelser kan i tillegg registreres som PREMIS-hendelser.
- PREMIS håndteres av `noark5_workflow/core/premis_logger.py` og executor-/workflowlaget.
- En operasjon skal aldri bygge sin egen separate workflow-PREMIS XML.
- Gyldige `eventType`-verdier følger DIAS_PREMIS v2.0: `Creation`, `Ingestion`, `Migration`, `Adjustment`, `Deletion`, `Disposal`.
- Teknisk kjørelogg og PREMIS har ulike formål.
- Noark 5-kilden skal ikke endres for å produsere PREMIS.

## Versjonering og releasehistorikk

Stabil baseline startet med `0.1.0`. Utviklingsserier bruker alpha-suffiks, for eksempel `0.1.1-a3`.

Alpha-/fikstrinn er midlertidige utviklingsidentifikatorer. Permanente release-notater samles per ferdig versjon i `docs/RELEASES.md`; det skal normalt ikke opprettes én permanent releasefil per `a1`, `a2`, `a3`, `a3.1` osv.

## Utdataområder og bevaringskilde

- Mottatt Noark 5-uttrekk er kilde/evidens og skal behandles som read-only.
- Genererte filer skal bare skrives i eksplisitt valgte arbeids-/utdataområder.
- Workflow-PREMIS skal følge eksplisitt workflow-/operasjonsutdata.
- Skill mellom arbeidsområde og finaliseringsområde for AIP.
- Ikke anta at alt i arbeidsområdet skal bevares i AIP.

## Generisk kode mot SIARD Workflow Manager

- Generiske forbedringer skal vurderes opp mot `SHARED-DEVELOPMENT.md` før de gjøres domenespesifikke.
- `SHARED-ROADMAP.md` skal oppdateres når en funksjon implementeres i ett prosjekt og er kandidat for det andre.
- Et eget felles GUI/core-repository opprettes ikke nå; kodebasene holdes løst koblet gjennom dokumenterte kontrakter, referanseimplementasjoner og tester.
