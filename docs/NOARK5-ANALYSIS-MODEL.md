# Noark 5-analysemodell – validering, kontroll og rapportering

## Grunnprinsipp
Arkivskaper er alltid ansvarlig for innholdet i uttrekket. Testing før levering utføres ofte av arkivskapers IT-/driftsmiljø eller systemleverandør på vegne av arkivskaper. Depotet foretar en selvstendig og pragmatisk validering av mottatt uttrekk og sender en forståelig rapport tilbake til arkivskaper for lesing og aksept.

Avvik dokumenteres. Nytt uttrekk er aktuelt først ved alvorlige struktur- eller innholdsmangler som gjør uttrekket utilstrekkelig som bevaringsversjon.

## Tre valideringsområder
### A – Noark 5-spesifikasjon mot Noark 5-uttrekk
Kontroll mot aktuell Noark-versjon: XML/XSD, struktur, obligatoriske elementer, relasjoner, standardverdier og andre normative krav.

### B – Noark 5-uttrekk mot innholdselementene i uttrekket
Intern konsistens og omfang: arkiv, arkivdeler, klassifikasjon, mapper, registreringer, dokumenter, journaler, endringslogg, parter, skjerming, kassasjon, sletting, konvertering, datoer og kryssfil-kontroller.

### C – Noark 5-uttrekk mot arkivskapers kontrollgrunnlag
Sammenligning mot opplysninger og forventninger fra arkivskaper, særlig avsluttede arkivdeler og forventet innhold i produksjonsbasen.

Depotet dokumenterer forskjeller. Arkivskaper vurderer og aksepterer innholdet eller sørger for korrigering dersom manglene er alvorlige.

## Standardverdier og generiske verdier
Standardverditesting og generisk opptelling skal kunne eksistere parallelt. Testdata fra ett uttrekk er evidens, ikke normativt grunnlag.

Observasjon, standardreferanse og faglig vurdering holdes adskilt.

## Individuelle analyser som grunnmodell
Hver faglig verdi skal så langt som mulig beregnes én gang av en individuell analyse eller kontroll. Resultatet lagres strukturert og gjenbrukes i views, validering, rapporter, vedlegg og senere API/database.

## U1 og U2
U1 og U2 beholdes som historisk krav-, sammenlignings- og regresjonsgrunnlag. De skal ikke være permanent grunnmodell eller parallelle beregningsprogrammer.

Målet er:

```text
individuelle analyser
        |
        v
kanoniske resultater
        |
        +--> samlet visning for hele uttrekket
        +--> samme relevante resultater per arkivdel
        +--> validerings-/kontrollvisninger
        +--> rapport og vedlegg
```

U01/U02 kan kjøres under utvikling/regresjon inntil alle nødvendige datapunkter kan rekonstrueres fra individuelle resultater.

## Views og rapportering
Views skal ikke utføre nye faglige beregninger. De setter sammen allerede beregnede resultater. Samme view kan brukes i depotets validering, hos arkivskaper, i hovedrapport og i vedlegg.

## Avvik og konsekvens
```text
testresultat / observasjon
        |
        v
avvik eller merknad
        |
        v
faglig vurdering
        |
        v
alvorlighetsgrad og konsekvens
```

Normal håndtering er dokumentasjon av avvik. Nytt uttrekk er unntaket ved alvorlige mangler.
