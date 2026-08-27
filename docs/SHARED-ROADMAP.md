# Shared roadmap

Dette er registeret for generiske funksjoner som er implementert eller planlagt i ett Workflow Manager-prosjekt og kan være nyttige i det andre.

Statusverdier: `Implemented in Noark`, `Implemented in SIARD`, `Implemented in both`, `Candidate`, `Planned`.

## DIAS pakketre: opprett mappe / legg til fil / legg til mappe

**Origin:** Noark 5 Workflow Manager  
**Status:** Implemented in Noark; candidate for SIARD

Felles verdi:

- opprette tom mappe i pakkeoppsettet,
- legge til enkeltfiler,
- legge til hele mapper rekursivt,
- velge målområde uten å endre kildeinnholdet,
- støtte administrative rapporter, depotoperasjoner, descriptive metadata og annet relevant innhold.

## Import av eksisterende DIAS metadata

**Origin/reference:** SIARD Workflow Manager  
**Status:** Implemented in both/adapted in Noark

Noark-implementasjonen er praktisk testet mot Arkade 5-generert `info.xml`.

## Sist brukte mapper

**Origin:** Noark 5 Workflow Manager  
**Status:** Implemented in Noark; candidate for SIARD

Husker blant annet kilde, utdata, metadataimport, legg-til-fil og legg-til-mappe.

## Sentral PREMIS-proveniens

**Reference implementation:** SIARD Workflow Manager  
**Status:** Implemented in both; Noark-adaptasjon fra v0.1.0

Felles retning:

- sentral logger,
- operasjoner deklarerer hendelsen i stedet for å skrive egen PREMIS,
- standardiserte event types,
- agent + objekt + outcome + event detail,
- teknisk workflow-logg og PREMIS holdes adskilt.

## Transfer + Verify + PREMIS

**Origin:** depotbehov identifisert i Noark-arbeidet  
**Status:** Planned

Felles omfang:

- overføring/kopiering fra A til B,
- eksplisitte kilde- og destinasjonsroller,
- SHA-256 før/etter,
- automatisk sammenligning,
- resultat og feil i vanlig workflow-logg,
- relevante PREMIS-hendelser,
- kilden skal ikke endres,
- støtte flyttbare/offline disker og distribuerte mottakskopier.

Typiske lagringsroller:

`ORIGINAL_RECEIVED -> QUARANTINE -> WORKING -> FINAL_AIP -> AIC_OUTPUT -> PRESERVATION_STORAGE`

## Working area -> Final AIP -> AIC finalization

**Origin:** Noark/depotarbeid  
**Status:** Planned

Arbeidsområdet skal kunne inneholde omfattende test-, debug- og mellomresultater. Final AIP-området skal være en eksplisitt kuratert delmengde. AIC skal bygges fra det som faktisk er godkjent for bevaring, ikke automatisk fra alt som finnes i arbeidsområdet.

## Ekstern sjekksumkontroll fra DIAS `<uuid>.xml`

**Origin:** depotarbeid  
**Status:** Planned

- les dokumentert checksum fra eksternt mottatt `info.xml/<uuid>.xml`,
- beregn checksum av mottatt `.tar`,
- sammenlign,
- dokumenter resultat og PREMIS-hendelse.

Den eksterne checksum-filen kan komme gjennom en annen kanal og være lagret i saksbehandlingssystemet.

## Native Noark 5 validation/reporting

**Origin:** Noark 5 Workflow Manager  
**Status:** Planned

- implementer kjente XPath/KDRS Query-kontroller som Python-kode,
- bruk én felles/strømmet analysemodell der store XML-filer leses minst mulig,
- U1/N5.101, U2/N5.102 og senere flere kontroller,
- strukturerte resultater og menneskelesbare rapporter,
- valider mot kjente XPath/KDRS Query-resultater.

Dette er Noark-spesifikk analyse, men rapport- og operasjonsrammeverket kan være generisk.

## Arkade 5 CLI som ekstern validator

**Origin:** eksisterende depotpraksis  
**Status:** Planned

Workflow Manager skal kunne:

- kalle Arkade 5 CLI uten å reimplementere Arkade,
- fange exit status/logg/rapportfiler,
- høste og analysere resultatene,
- sammenligne med egne Noark-kontroller,
- bruke et generisk mønster for eksterne validatorer som også kan gjenbrukes i SIARD.

Tidligere praksis med Arkade 5 CLI/PRONOM PUID-analyse av utpakket SIARD-innhold er viktig referanse for dette mønsteret.

## Pipeline / end-to-end depotworkflow

**Origin:** Noark 5 Workflow Manager  
**Status:** Planned

Pipeline er orkestrering, ikke én stor monolittisk funksjon. Den skal kunne sette sammen:

- transfer/verify mellom lagringssoner,
- karantene/AV-relaterte steg,
- utpakking/forberedelse der container krever det,
- Arkade 5 CLI,
- native Noark-validering,
- rapportering,
- finalisering av AIP,
- DIAS/AIC-pakking,
- sluttkontroll og PREMIS.

Containerlogikk skal eies av relevante pakkeoperasjoner, ikke hardkodes i Pipeline-knappen.

## Recursive jobs / batch orchestration

**Origin:** tidligere Python-jobbrammeverk for SIARD og mulige Noark-datasett  
**Status:** Planned

Metodisk mønster:

`discover -> prequalify -> skip/run/fail with reason -> execute -> per-job result -> aggregate`

Krav:

- rekursiv discovery med konfigurerbart navnemønster,
- prequalify før tung kjøring,
- hopp over hvis allerede behandlet eller nødvendig innhold mangler,
- per-jobb logg/rapport,
- samlet status/statistikk,
- selektiv retry,
- store objekter må ikke kopieres, pakkes ut eller hashes bare fordi de ble oppdaget,
- tung I/O skal være eksplisitt og stream-basert.

Dette er viktig både for mange mindre deler og svært store uttrekk, inkludert flerterabyte-materiale.
