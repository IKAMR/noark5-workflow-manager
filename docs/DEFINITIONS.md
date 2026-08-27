# Definisjoner

## Noark 5-uttrekk

System-/uttrekksnivået som består av Noark 5-metadata, skjemaer og dokumentinnhold. Mottatt uttrekk behandles som bevaringsbevis og skal normalt ikke endres av analyse/validering.

## DIAS SIP/AIC

Pakkenivået rundt innhold som skal overføres eller bevares. Pakkingen beskriver og omslutter innholdet, og kan suppleres med andre filer og mapper i pakken.

## Workflow-/kjørelogg

Detaljert teknisk og operativ historikk over alt som kjøres. Alle operasjoner og tester skal fremgå her, også når de ikke blir egne PREMIS-hendelser.

## PREMIS-proveniens

Maskinlesbar dokumentasjon av relevante bevarings- og valideringshendelser. Workflow-PREMIS er separat fra vanlig kjørelogg og fra package-level PREMIS/METS generert som del av DIAS-pakkestrukturen.

## PREMIS event

Én relevant hendelse, med type, tidspunkt, detalj, outcome og kobling til agent og objekt.

## PREMIS object

Objektet hendelsene gjelder. I a10 er dette det valgte Noark 5-uttrekket identifisert med mappenavn og format `NOARK-5`.

## PREMIS agent

Programvaren som utførte hendelsen. I a10: `Noark 5 Workflow Manager` med versjon.

## PREMIS outcome

Resultatkode for hendelsen. DIAS-konvensjonen som brukes av den generiske loggeren er `0` for suksess og `1` for feil.

## content/

DIAS-området for innhold. I Noark 5 Workflow Manager inngår det valgte Noark 5-uttrekket her. Brukeren kan også legge til annet relevant innhold når arbeidsprosessen krever det.

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
