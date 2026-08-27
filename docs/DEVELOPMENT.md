# Utviklingsregler

Før analyse eller endring av kode i dette repositoriet:

1. Les `docs/DEVELOPMENT.md`.
2. Les `docs/ARCHITECTURE.md` der den finnes og er relevant.
3. Les `docs/INTERFACE.md` ved endringer i grensesnitt eller kontrakter.
4. Les `docs/DEFINITIONS.md` ved endringer som berører begreper og lagdeling.
5. Les `docs/TESTING.md` ved endringer som krever ny eller endret validering.
6. Les `docs/CODE-MAP.md` for å finne riktig lag og dataflyt.
7. Les `docs/SHARED-DEVELOPMENT.md` og `docs/SHARED-ROADMAP.md` før generiske workflow-/depotendringer som også kan være relevante for SIARD Workflow Manager.
8. Behandle dokumentert arkitektur som målbildet. Kontroller samtidig den faktiske koden før endringer gjøres.

## Endringsprinsipp

- Bevar fungerende funksjonalitet og gjør den minste nødvendige endringen.
- Ikke erstatt et etablert GUI-panel i sin helhet bare for å legge til en kontroll eller funksjon.
- Noark 5-uttrekket og DIAS SIP/AIC er separate lag. DIAS-pakking kan supplere pakkens innhold og metadata uten å endre kildefilene på disk.
- Mottatt Noark 5-uttrekk behandles som bevaringsbevis og skal som hovedregel analyseres, valideres og dokumenteres uten å endres.
- Nye funksjoner skal ha automatiserte tester når det er praktisk mulig.
- Før commit av en alpha: kjør `test.bat`, deretter praktisk test via `start.bat`.

## Workflow logging og PREMIS-proveniens

Dette er en arkitekturregel for hele prosjektet:

- **Alle operasjoner/tester** skal fremgå av vanlig workflow-/kjørelogg.
- **Relevante bevarings-, validerings-, migrerings-, slettings- og pakkingshendelser** kan i tillegg registreres som PREMIS-hendelser.
- PREMIS skal håndteres av den sentrale mekanismen i `noark5_workflow/core/premis_logger.py` og executor-/workflowlaget.
- En operasjon skal aldri bygge sin egen separate workflow-PREMIS XML.
- Operasjonen deklarerer kun om den skal registreres (`premis_record`), gyldig `premis_event_type`, valgfri `premis_event_label`, og kan overstyre `premis_detail()` / `premis_should_record()`.
- Gyldige `eventType`-verdier følger DIAS_PREMIS v2.0: `Creation`, `Ingestion`, `Migration`, `Adjustment`, `Deletion`, `Disposal`.
- Teknisk kjørelogg og PREMIS har ulike formål. PREMIS erstatter ikke detaljert operatør-/debuglogg.
- Noark 5-kilden skal ikke endres for å produsere PREMIS; proveniensfilen er side-/administrativ dokumentasjon.

Implementasjonen er basert på det generiske PREMIS-mønsteret i SIARD Workflow Manager, tilpasset Noark 5-objekt og Noark 5 Workflow Manager-agent.

## Versjonering

Stabil baseline er `0.1.0` og Git-tag `v0.1.0`. Nye utviklingsserier bruker alpha-suffiks, for eksempel `0.2.0-a1`.

## Utdataområder og bevaringskilde

- Mottatt Noark 5-uttrekk er kilde/evidens og skal behandles som read-only.
- Når brukeren har valgt en utdatamappe, skal genererte filer bare skrives i eksplisitt valgte arbeids-/utdataområder, aldri ved siden av eller inne i kilden som implisitt fallback.
- Workflow-PREMIS skal følge eksplisitt workflow-/operasjonsutdata. DIAS-pakking bruker den valgte DIAS-utdatamappen.
- Skill mellom **arbeidsområde** (alle tester, debug, mellomresultater og rapporter) og **finaliseringsområde for AIP** (kuratert delmengde som faktisk skal inngå i endelig AIC/AIP).
- Ikke anta at alt som finnes i arbeidsområdet skal bevares i AIP. Finalisering skal være et eksplisitt steg.


## Generisk kode mot SIARD Workflow Manager

- Generiske forbedringer skal vurderes opp mot `SHARED-DEVELOPMENT.md` før de gjøres domenespesifikke.
- `SHARED-ROADMAP.md` skal oppdateres når en funksjon implementeres i ett prosjekt og er kandidat for det andre.
- Et eget felles GUI/core-repository opprettes ikke nå; kodebasene holdes løst koblet gjennom dokumenterte kontrakter, referanseimplementasjoner og tester.
