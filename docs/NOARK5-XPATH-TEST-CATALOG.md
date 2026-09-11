# Noark 5 XPath-testkatalog 2026

Mastergrunnlaget `IKAMR/KDRS_Query/doc/xml-queries_noark5_2026-05-26.txt` er modellert som en JSON-katalog. Hver legacy-jobb har stabil intern test-ID, original `job_id`, testpunkt, `job_enabled`, kilde-XML, subsystem, Noark-versjonsmerking, tags, scope og strukturert kjøredefinisjon.

Kjøring produserer et strukturert resultatsett under `Arbeid – operasjoner/noark5_tests/xpath/<timestamp>/` med `definitions.json`, `index.json`, `test-events.jsonl` og én JSON-fil per test. Legacy-deaktiverte tester får isolert status når `include_disabled=True`, men kjøres ikke. Manglende `loependeJournal.xml`, `offentligJournal.xml` eller `endringslogg.xml` gir `source_missing`, ikke feil på hele kjøringen.

## Standardverdier og generiske tellere

Testkatalogen skal ikke utformes etter hvilke verdier som tilfeldigvis finnes i ett bestemt testuttrekk. Et uttrekk brukes til verifikasjon og regresjon, men er ikke fasit for hvilke kontroller katalogen skal støtte.

Der Noark 5 v3.1, 4.0 eller 5.0 definerer standardverdier, skal disse kunne testes eksplisitt. Generiske tellere og fordelinger skal samtidig beholdes der de gir relevant informasjon.

Standardverdier og observerte verdier er komplementære:

- standardverdikontroller viser forekomst av kjente verdier for aktuell Noark-versjon,
- generiske kontroller viser alle faktisk observerte verdier,
- en observert ikke-standard verdi skal ikke automatisk klassifiseres som feil av telleren,
- faglig vurdering og alvorlighetsgrad kommer i et senere lag.

Standardverdier og versjonstilknytning bør så langt som mulig beskrives i JSON-definisjoner, ikke hardkodes i Python.

## U1 og U2

U01 og U02 beholdes i katalogen som historisk referanse og utviklings-/regresjonsgrunnlag. De skal ikke være den permanente beregningsmodellen.

Målet er at individuelle analyser produserer kanoniske resultater én gang, og at U1/U2-lignende lister og tabeller senere settes sammen fra disse resultatene for hele uttrekket eller per arkivdel.

U01/U02 kan tas ut av ordinær kjøring når nødvendige datapunkter kan rekonstrueres fra individuelle analyser. Dekningskartleggingen ligger i `docs/NOARK5-U1-U2-COVERAGE-MAPPING.md`.

## a21 – kvalitetssikring mot legacy-grunnlaget

a21 viderefører KDRS Query-sporbarheten, men skiller mellom:

- original legacy-definisjon,
- bekreftet feil eller quirk i legacy-grunnlaget,
- normalisert Noark 5-testpunkt eller scope,
- bevisst utvidelse i Workflow Manager,
- generisk resultat som supplerer eksplisitte legacy-tellere.

Historiske feil skal ikke kopieres videre som faglig sannhet, men original betydning bevares i kildesporbarheten.

## Regresjon mellom arbeidsversjoner

Når samme Noark 5-uttrekk kjøres med to arbeidsversjoner, skal forskjellene brukes til å kontrollere implementasjonen – ikke til å redefinere testkatalogen.

Sammenligningen skal kontrollere:

- uendrede faglige resultater,
- tilsiktede endringer i resultatstruktur,
- `job_id`, N5-testpunkt, navn, kilde-XML, scope, tags og versjonsmetadata,
- U1/U2 som regresjonsreferanse så lenge de fortsatt kjøres,
- at standardverditellere og generiske fordelinger ikke utilsiktet forsvinner,
- `test.started`, `test.finished`, `test.failed` og `test.skipped` med korrekt identitet, rekkefølge og varighet.

Faktiske antall og kodeverdier i ett testuttrekk er evidens for den konkrete kjøringen, ikke normative definisjoner for fremtidige uttrekk.
