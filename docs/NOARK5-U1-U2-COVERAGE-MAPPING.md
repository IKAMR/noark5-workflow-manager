# U1/U2 – dekningskartlegging mot individuelle Noark 5-analyser

## Formål
U01/U02 brukes som historisk referanse og regresjonsgrunnlag. Målet er å dokumentere hvilke datapunkter som allerede finnes som individuelle analyser og hvilke som mangler før U01/U02 kan tas ut av ordinær kjøring.

## Dekningsstatus
- `COVERED` – tilsvarende individuell analyse finnes
- `PARTIAL` – deler finnes, men ikke hele behovet eller begge scope
- `MISSING` – datapunktet finnes foreløpig bare i U01/U02
- `REFERENCE` – identitets-/presentasjonsdata som skal kunne hentes uten egen U-jobb

## Hovedkartlegging

| Område | Legacy/N5 | Scope | A/B/C | Individuelt grunnlag | Status |
|---|---|---|---|---|---|
| Arkiv, antall | C01 / N5.04 | hele | B | C01 | COVERED |
| Arkivskaper, antall | C01 | hele | B | C01 | COVERED |
| Arkividentitet og metadata | U01 | hele | B | native entity-modell | PARTIAL |
| Arkivdeler, antall | C02 / N5.05/06 | hele | B | C02 | COVERED |
| Arkivdelidentitet/status/periode | U01/U02 | arkivdel | B | native arkivdelmodell | PARTIAL |
| Arkivdel hovedtall | C02/U02 | begge | B | C02 + per-arkivdel-analyser | PARTIAL |
| Klassifikasjonssystem | C05 / N5.07 | begge | B | C05 + C05.01_R3 | COVERED |
| Klasser | C06 / N5.08 | hele | B | C06 | COVERED |
| Klasse+underklasse+mappe | C10 / N5.12 | begge | A/B | C10 + C10_R5 | COVERED |
| Klasse+underklasse+registrering | N5.19.01 | hele | A/B | C-katalog | COVERED |
| Mapper totalt/type | C08 | hele | B | C08 | COVERED |
| Mapper uten spesialisering | C08 / N5.15.01 | hele | A/B | C08 | COVERED |
| Mappestatus standard | C13 / N5.15 | begge | A/B | C13 + C13.01 | COVERED |
| Mappestatus generisk | C13 / N5.15.02 | begge | B | C13 + C13.01 | COVERED |
| Mapper per år | C09 / N5.11 | begge | B | C09 + C09_R4 | COVERED |
| Registreringer totalt/type | C14 / N5.16 | hele | B | C14 | COVERED |
| Registrering uten dokumentbeskrivelse | C16 / N5.21 | begge | A/B | C16 + C16_R6 | COVERED |
| Journalposttype standard | C15 / N5.17 | begge | A/B | C15 + C15.01 | COVERED |
| Journalposttype generisk | C15 / N5.17.01 | begge | B | C15 + C15.01 | COVERED |
| Løpende journal | H01-H04 | hele | B | H01-H04 | COVERED |
| Offentlig journal | H05-H07 | hele | B | H05-H07 | COVERED |
| Arkivstruktur mot journalfiler | I01-I02 / N5.60 | hele | B | I01-I02 | COVERED |
| Endringslogg | J01 / N5.61 | hele | B | J01 | COVERED |
| Sakspart/part | F01 / N5.35 | begge | A/B | F01 + U2-grunnlag | PARTIAL |
| Merknader | F02 / N5.36 | hele | B | F02 | COVERED |
| Kryssreferanser | F03 / N5.37 | hele | B | F03 | COVERED |
| Presedens | F04 / N5.38 | hele | B | F04 | COVERED |
| Korrespondansepart | F05 / N5.39 | hele | B | F05 | PARTIAL |
| Avskrivning | F06 / N5.40 | hele | A/B | F06 | COVERED |
| Dokumentflyt | F07 / N5.41 | hele | B | F07 | COVERED |
| Skjerming | F08 / N5.42 | begge | A/B | F08 + U2 | PARTIAL |
| Gradering/grad | F09 / N5.43 | hele | A/B | F09 | COVERED |
| Kassasjon | F10 / N5.44 | begge | A/B | F10 + U2 | PARTIAL |
| Utført kassasjon | F11 / N5.45 | begge | B | F11 + U2 | PARTIAL |
| Konvertering | F12 / N5.46 | hele | B | F12 | PARTIAL |
| Sletting | F13 / N5.47 | begge | A/B | F13 + U2 | PARTIAL |
| Virksomhetsspesifikke metadata | L02 / N5.65 | hele | A/B | L02 a21 | COVERED |

## Datapunkter som fortsatt mangler eller er bare delvis dekket

1. Datointervaller som selvstendige, gjenbrukbare analyser:
   - arkivdel opprettet/avsluttet
   - mappe opprettet/avsluttet
   - saksdato
   - møtedato
   - registrering arkivert
   - dokumentbeskrivelse opprettet

2. Dokumentrelaterte fordelinger:
   - `tilknyttetRegistreringSom` generisk
   - dokumentnummer
   - versjonsnummer
   - dokumentstatus med versjonsspesifikke standardverdier
   - dokumentmedium
   - variantformat
   - dokumenttype

3. Fil-/formatstatistikk:
   - filstørrelsesintervaller
   - snitt, maksimum og sum
   - format
   - formatdetaljer

4. Konverteringsdetaljer:
   - konvertert fra format
   - konvertert til format
   - konverteringsverktøy

5. Per-arkivdel-varianter av flere eksisterende hele-uttrekket-analyser.

6. Normalisert maskinlesbar modell for standardverdier per Noark 5 v3.1, 4.0 og 5.0.

## U2-vurdering
U2 representerer i hovedsak de samme faglige områdene som U1, men per arkivdel. Den bør derfor ikke erstattes av et nytt parallelt U2-system.

Samme individuelle analyse bør kunne materialiseres med:
- `whole_extraction`
- `archive_part`

## Område C
U1/U2 gir ikke reell dekning av område C.

Område C bør modelleres separat som sammenligning mellom kanoniske uttrekksresultater og eksternt kontrollgrunnlag fra arkivskaper, for eksempel:

```text
archive_part.system_id
expected.folder_count
observed.folder_count
difference
source_of_expected_value
creator_comment
depot_assessment
acceptance_status
```

Denne sammenligningen skal ikke bygges inn i selve XPath-testen.

## Konklusjon
U01/U02 bør foreløpig beholdes kun for utvikling/regresjon. De kan tas ut av ordinær kjøring når de manglende individuelle analysene over er dekket og resultatene kan rekonstruere U1/U2-informasjonsbehovet.
