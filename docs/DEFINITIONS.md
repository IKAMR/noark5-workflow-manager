# Definisjoner

## Noark 5-uttrekk

System-/uttrekksnivået som består av Noark 5-metadata, skjemaer og dokumentinnhold. Mottatt uttrekk behandles som bevaringsbevis og skal normalt ikke endres av analyse/validering.

Noark 5-nivået skal holdes adskilt fra et eventuelt DIAS-pakkelag rundt uttrekket. Uttrekksformatet omfatter også referanser og sjekksummer som inngår i den selvdokumenterende strukturen.

## DIAS SIP/AIC

Pakkenivået rundt innhold som skal overføres eller bevares. Pakkingen beskriver og omslutter innholdet, og kan suppleres med andre filer og mapper i pakken.

DIAS er et separat nivå over uttrekksformat som Noark 5 eller SIARD. For Noark 5 ligger selve uttrekket i TAR, mens DIAS-metadata-XML er en separat komponent på DIAS-nivået. Se `ARCHITECTURE.md` for bevarings-, validerings- og repakkingsprinsippene.

## Workflow-/kjørelogg

Detaljert teknisk og operativ historikk over alt som kjøres. Alle operasjoner og tester skal fremgå her, også når de ikke blir egne PREMIS-hendelser.

## PREMIS-proveniens

Maskinlesbar dokumentasjon av relevante bevarings- og valideringshendelser. Workflow-PREMIS er separat fra vanlig kjørelogg og fra package-level PREMIS/METS generert som del av DIAS-pakkestrukturen.

## PREMIS event

Én relevant hendelse, med type, tidspunkt, detalj, outcome og kobling til agent og objekt.

## PREMIS object

Objektet hendelsene gjelder. I v0.1.0 er dette det valgte Noark 5-uttrekket identifisert med mappenavn og format `NOARK-5`.

## PREMIS agent

Programvaren som utførte hendelsen. I a10: `Noark 5 Workflow Manager` med versjon.

## PREMIS outcome

Resultatkode for hendelsen. DIAS-konvensjonen som brukes av den generiske loggeren er `0` for suksess og `1` for feil.

## content/

DIAS-området for innhold. I Noark 5 Workflow Manager inngår det valgte Noark 5-uttrekket her. Brukeren kan også legge til annet relevant innhold når arbeidsprosessen krever det.

I normalformen for Noark 5 Workflow Manager ligger roten til ett Noark 5-uttrekk direkte i `content`. Se `ARCHITECTURE.md` for unntak og normalisering/repakking.

## Original SIP/TAR

Mottatt pakket representasjon som som hovedregel bevares urørt og behandles read-only. Workflow Manager skal kunne lese relevant innhold direkte fra TAR uten automatisk full uttrekking.

## Normalisert/repakket SIP

Ny representasjon produsert når mottatt intern struktur må normaliseres, for eksempel når uttrekksroten ligger for dypt eller flere uttrekk må splittes. Repakking er en sporbar transformasjon med kobling til mottatt original.

## Lokal persistens

Applikasjonens lokale varige lagring av tilstand og data som trengs under distribuert og gjenopptakbar behandling. SQLite er foretrukket kandidat, men endelig datamodell og skjema er ikke besluttet.

## Ekstern datakilde / adapter

Et eksternt regneark, en database, et API eller et fagsystem som utveksler relevante data med Workflow Manager gjennom mapping mot en generisk intern modell. En bestemt ekstern master skal ikke definere produktets datamodell.

## Programmatisk styringsgrensesnitt

Maskinrettet inngang til Workflow Managers jobb- og workflowfunksjoner uten krav om aktivt desktop-GUI. CLI er planlagt første eksponering; framtidig nettverks-API eller andre eksterne stimuli kan bruke samme underliggende modell.

## administrative_metadata/

DIAS-området for administrativ metadata.

## repository_operations/

Område under `administrative_metadata/` for dokumentasjon av operasjoner i depotarbeidet, eksempelvis rapporter, logger, PREMIS-proveniens og kontrollresultater.

## descriptive_metadata/

DIAS-området for beskrivende metadata.

## Arbeidsområde

Depotets område for analyser, tester, debug, logger, rapporter og mellomresultater. Innhold her er ikke automatisk del av endelig AIP.

## AIP-finaliseringsområde

Eksplisitt kuratert delmengde som er godkjent for langtidsbevaring og som skal inngå i AIC/AIP. Finalisering skiller bevaringsverdig dokumentasjon fra midlertidig arbeidsmateriale.

## SIP og AIP

**SIP** er innsendingspakken ved overføring til depot. Når materialet er tatt inn i bevaringsforvaltningen, er den bevarte representasjonen en **AIP**. At de samme bitene kan videreføres uendret gjør ikke begrepene identiske; rollen/livssyklusstadiet er forskjellig.

## Original received

Mottatt/original kopi på distribuert eller offline lagring. Behandles som read-only bevaringsbevis.

## Quarantine

Område for karantene/antivirusperiode før materialet flyttes videre til arbeidsområdet.

## Working area

Arbeidsområde som kan inneholde omfattende tester, debug, mellomresultater, rapporter og alternative kopier. Alt her skal ikke automatisk inn i AIP.

## Final AIP

Eksplisitt kuratert innhold som er godkjent for bevaring og som skal inngå i den endelige bevaringspakken.

## AIC output

Utdataområdet der AIC/container med AIP produseres. SIP beskriver innsendingsrollen/stadiet; innhold som er overtatt til bevaring omtales som AIP selv om byteinnhold kan være identisk med mottatt materiale.

## Recursive job / batch job

Metodisk kjøring over mange kandidater: discovery, prequalification, skip/run/fail med begrunnelse, ordinær workflow-kjøring og aggregert resultat.
