# Utviklingsregler

Før analyse eller endring av kode i dette repositoriet:

1. Les `docs/DEVELOPMENT.md`.
2. Les `docs/ARCHITECTURE.md` der den er relevant.
3. Les `docs/INTERFACE.md` ved endringer i grensesnitt eller kontrakter.
4. Les `docs/DEFINITIONS.md` ved endringer som berører begreper og lagdeling.
5. Les `docs/TESTING.md` ved endringer som krever ny eller endret validering.
6. Les `docs/CODE-MAP.md` for å finne riktig lag og dataflyt.
7. Les `docs/RUNTIME-ENVIRONMENTS.md` ved endringer i installasjon, oppstart, filstier, brukerdata, eksterne programmer, packaging, server/worker eller plattformstøtte.
8. Les `docs/SHARED-DEVELOPMENT.md` og `docs/SHARED-ROADMAP.md` før generiske workflow-/depotendringer som også kan være relevante for SIARD Workflow Manager.
9. Behandle dokumentert arkitektur som målbildet. Kontroller samtidig den faktiske koden før endringer gjøres.

## Endringsprinsipp

- Bevar fungerende funksjonalitet og gjør den minste nødvendige endringen.
- Ikke erstatt et etablert GUI-panel i sin helhet bare for å legge til en kontroll eller funksjon.
- Noark 5-uttrekket og DIAS SIP/AIC er separate lag.
- Mottatt Noark 5-uttrekk behandles som bevaringsbevis og skal som hovedregel analyseres, valideres og dokumenteres uten å endres.
- Nye funksjoner skal ha automatiserte tester når det er praktisk mulig.
- Før commit av en alpha: kjør `test.bat`, deretter praktisk test via `start.bat`.

## Kjøremiljø og portabilitet

- Windows desktop er dagens testede baseline.
- Ikke dokumenter Linux, macOS, server eller andre miljøer som støttet før installasjon, oppstart og relevant praktisk test er etablert.
- Ikke legg ny domenelogikk i `.bat`, `.sh` eller packaging.
- Unngå hardkodede Windows-stier i core/operations.
- Bruk plattformuavhengige Python-API-er og `pathlib` når mulig.
- Runtime-state og brukerinnstillinger skal på sikt ligge i egnet per-user application-data-område, ikke være avhengig av repository/installasjonsmappen.
- Eksterne programmer skal kapsles i adaptere med konfigurerbar executable/path.
- Core/operations skal ikke avhenge av GUI.
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
