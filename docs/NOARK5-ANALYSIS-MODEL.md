# Noark 5-analysemodell – U1/U2 som kravgrunnlag

## Prinsipp

U1 og U2 brukes som krav- og referansegrunnlag for hvilke data og kontroller som skal
kunne produseres. De brukes **ikke** som to hardkodede analyseprogrammer.

Arkitekturen skilles i tre lag:

```text
ekstern definisjon
      |
      v
definisjonsdrevet test-/analysemotor
      |
      v
kanonisk strukturert resultat
      |
      +--> U1-lignende samlet visning
      +--> U2-lignende visning per arkivdel
      +--> kontrollrapport
      +--> hovedrapport/vedlegg
      +--> senere API/database
```

## Eksterne definisjoner

Første analysetrinn ligger i:

`config/noark5/analysis/u1_u2_core_arkiv_arkivdel.json`

XPath, felt og tellere ligger her, ikke i Python-motoren. Første trinn omfatter
Arkiv og Arkivdel og bygger på det U1/U2-materialet som allerede er dokumentert
i prosjektet (C01/C02/U01/U02-referansene).

Neste U1/U2-deler skal legges til definisjonene stegvis. Python-motoren skal bare
endres dersom definisjonsspråket faktisk trenger en ny generell mekanisme.

## Grunnmodell kontra rapportering

`definition_engine.py` produserer en kanonisk resultatmodell med:

- `summary.entity_counts`
- `entities.<entity>[]`
- `fields`
- `metrics`
- `children`

Rapportvisninger beskrives separat i:

`config/noark5/report_views/u1_u2_views.json`

a15 step1 genererer foreløpig ikke U1/U2-dokumenter. Filen låser bare skillet
mellom analysegrunnlag og senere rapportvisninger.

## Resultatmapper

Noark 5-testresultater samles under:

```text
<Arbeid – operasjoner>/
└── noark5_tests/
    ├── schema/
    └── native/
```

`schema/` inneholder XML/XSD-resultater.

`native/` inneholder Workflow Managers egne Noark 5-analyser.

Eksterne validatorer, for eksempel Arkade 5, får egne tydelige undermapper med
verktøy/versjon når adapteren implementeres.
