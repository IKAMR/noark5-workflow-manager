# Data Workflow Manager – arkitekturretning

## Status

Dette dokumentet er autoritativt for generaliseringsretningen som ble besluttet i Noark 5 Workflow Manager v0.1.2-a12.

Dette er en **gradvis arkitekturendring**, ikke en ferdig repository-splitt.

Noark 5 Workflow Manager skal fortsatt utvikles som fungerende Noark 5-verktøy. Arbeidet med et generisk rammeverk skal ikke forsinke praktisk behov for analyse, validering, rapportering og DIAS AIC-pakking.

Planlagt framtidig hovedrepository:

`https://github.com/IKAMR/data-workflow-manager`

IKAMR tar initiativ til og ansvar for dette hovedrepositoryet nå. Endelig langsiktig forvaltningsmodell er ikke låst, og andre fagmiljøer skal kunne arbeide gjennom forks og bidra tilbake.

SIARD Workflow Manager er et selvstendig søsterprosjekt og en viktig referanseimplementasjon. Data Workflow Manager skal ikke omskrive eierskap eller historikk for SIARD Workflow Manager.

## Repository-strategi

Vi oppretter ikke en parallell full kodebase ved å kopiere Noark 5 Workflow Manager.

Ønsket retning når grensen er tilstrekkelig moden er:

```text
nå:
IKAMR/noark5-workflow-manager
        |
        | gradvis generalisering
        v
Noark 5 + generisk runtime

senere:
rename / viderefør Git-historikken
        |
        v
IKAMR/data-workflow-manager
        |
        +-- generisk runtime
        +-- GUI / CLI
        +-- profiler/extensions
        +-- Noark 5 som første praktiske profil

deretter:
nytt/tynt IKAMR/noark5-workflow-manager
        |
        +-- peker til Data Workflow Manager
        +-- dokumenterer Noark 5-bruk/profil
        +-- eventuelt distribusjons-/wrapperlag
```

Repository-rename skal ikke gjøres i a12.

Kriteriet for senere rename er at den kjørende applikasjonen reelt kan forstås som et generisk rammeverk der Noark 5 er en profil/extension, ikke en forutsetning i Core.

## Grunnmodell

Data Workflow Manager utfører oppgaver på en input. Input vurderes og behandles gjennom operasjoner og ender i output med eller uten dokumentasjon.

```text
Input
  |
  v
identify / inspect
  |
  v
operations / workflow
  |
  +--> structured results
  +--> reports
  +--> provenance / logs
  |
  v
Output
```

Den innerste runtime-kjernen skal ikke kjenne begrepene Noark 5, SIARD, ADDML eller DIAS.

## Arkitekturlag

### 1. Runtime / orchestration

Generisk runtime eier blant annet:

- Job / jobbliste
- Workflow
- kontrollpunkter og fortsettelse
- preflight
- JobRunner / BatchRunner
- executor-grense
- logging
- status/resultat-kontrakter
- input/output-kontekst
- GUI / CLI / senere API som klienter over samme tjenester

### 2. Generiske operasjoner

Aktuelle generiske operasjonstyper:

- fil- og mappekopiering
- flytting/migrering mellom lagringsområder
- checksum og verify
- fil-/mappeinspeksjon
- analyse gjennom eksternt definert evaluator/kriteriesett
- generisk kjøring av eksternt verktøy
- TAR/ZIP pakking og utpakking
- generisk rapport-rendering
- transformasjons-/migreringsorkestrering

At en operasjonstype er generisk betyr ikke at alle kriteriene er innebygd i rammeverket.

## Definitions / extensions

Definisjonslaget bestemmer hva som skal vurderes, transformeres eller produseres.

Eksempler:

- kriterier og regler
- schemas
- mappings
- rapportdefinisjoner/templates
- pakkedefinisjoner
- ekstern Python-kode
- eksterne programmer
- domenespesifikke operasjoner

Kriterier bør skilles fra kode når det er praktisk. Da kan faglige krav endres uten at kjøringsrammeverket må endres.

Ekstern kode kan fortsatt være hardkodet mot sitt eget fagområde. Kravet er at **Data Workflow Manager Core ikke hardkoder domenet**.

## Profiles

En profil setter sammen relevante definitions/extensions/operasjoner til et brukbart domeneoppsett.

Eksempler:

- Noark 5
- SIARD
- ADDML 7.3
- senere andre formater og arbeidsflyter

En profil er ikke nødvendigvis en separat applikasjon.

Eksempel:

```text
Noark 5 profile
    |
    +-- Noark source
    +-- Noark validation
    +-- Noark reporting
    +-- Arkade adapter
    +-- generic checksum
    +-- generic transfer
    +-- DIAS packaging extension
```

DIAS er derfor ikke en del av Noark 5 Core. Det er et spesialisert pakkelag som kan brukes sammen med flere profiler.

## Transformasjon og migrering

Migrering skal være en førsteklasses operasjonstype.

```text
Source
  |
  v
validate source
  |
  v
map
  |
  v
transform / generate
  |
  v
validate target
  |
  v
compare / reconcile
  |
  +--> report
  +--> provenance
  |
  v
Target
```

Aktuelle retninger omfatter blant annet:

- ADDML 7.3 -> SIARD
- SIARD -> SIARD, inkludert dialekt-/normaliseringsløp
- Noark 5 -> SIARD
- framtidig generering av Noark 5-uttrekk
- andre format- og representasjonsmigreringer

Source og target trenger ikke tilhøre samme domene.

## a12 – implementert arkitekturbevis

a12 skal ikke gjøre hele kodebasen generisk.

Følgende er implementert og testet:

### Profile boundary

`app/profile.py` introduserer `WorkflowProfile`.

Noark 5 setter sammen dagens operasjoner i:

`noark5_workflow/profile.py`

```text
NOARK5_PROFILE
      |
      v
WorkflowProfile
      |
      v
OperationRegistry
```

`noark5_workflow/app.py` bygger registry gjennom profilen i stedet for å registrere konkrete operasjoner direkte.

### Registry boundary

`noark5_workflow/core/registry.py` kjenner ikke konkrete Noark 5-operasjoner.

Registry bærer:

- operasjoner
- kategori-rekkefølge
- kategoriaccent/presentasjonsmetadata

GUI-et leser denne informasjonen fra registry/profilen.

### Source boundary

`noark5_workflow/core/source.py` definerer den minimale generiske `WorkflowSource`-kontrakten.

Foreløpig kreves bare:

```text
root
```

`OperationContext.input_root` er den generiske inngangen for runtime/executor.

Det eksisterende `extraction_root` beholdes for kompatibilitet med:

- `.n5jobs`
- GUI
- CLI
- eksisterende Noark 5-operasjoner
- eksisterende tester

a12 skal ikke masseomdøpe dette feltet.

### Domenelaget forblir domenespesifikt

Dette er tilsiktet:

```text
noark5_workflow/sources/noark5_extraction.py
noark5_workflow/operations/metadata_inventory.py
noark5_workflow/operations/analyse_arkivstruktur.py
```

kan fortsatt kjenne Noark 5.

Målet er:

> generisk runtime, eksplisitt domenelag

ikke:

> domenekode som later som den er formatnøytral

## Kodekart for den nye grensen

```text
Desktop GUI -------------------+
                               |
CLI ---------------------------+
                               |
                               v
                     generic runtime
        Preflight / BatchRunner / JobRunner
                               |
                               v
                         Executor
                               |
                               v
                     OperationRegistry
                               ^
                               |
                        WorkflowProfile
                               ^
                               |
                   +-----------+-----------+
                   |                       |
              Noark 5 profile        future profiles
                   |                  SIARD / ADDML / ...
                   v
           Noark operations
                   |
                   v
             Noark source
```

Source-grensen mot runtime:

```text
domain source object
       |
       | root
       v
WorkflowSource / source_root()
       |
       v
OperationContext.input_root
       |
       v
generic executor/runtime
```

## Hva a12 uttrykkelig ikke gjør

Ikke del av a12:

- dynamisk plugin-discovery/installasjon
- eget plugin package-format
- repository-rename
- kopiering til et nytt parallelt hovedrepo
- bred omdøping av `noark5_workflow`
- omskriving av alle eksisterende Noark-operasjoner
- ny SQLite-modell
- ny server/runtime
- ny API-tjeneste
- migreringsmotor
- generisk rapportmotor

Disse vurderes senere når konkrete funksjonsbehov gjør grensen nødvendig.

## Prioritet etter a12

Etter at a12 er låst, skal hovedprioriteten tilbake til praktisk Noark 5-leveranse:

```text
Noark 5 input
    |
    v
analyse / validation
    |
    v
structured results
    |
    v
reporting
    |
    v
DIAS AIC
    |
    v
verification / documentation
```

Ny generisk funksjonalitet skal utformes slik at den senere kan flyttes naturlig til Data Workflow Manager, men dette skal ikke blokkere nødvendig Noark 5-funksjonalitet.

## Dokumentasjonsregel videre

Når eksisterende `ARCHITECTURE.md`, `CODE-MAP.md`, `SHARED-DEVELOPMENT.md` og `SHARED-ROADMAP.md` senere oppdateres, skal denne retningen innarbeides kirurgisk.

Korrekte eksisterende beskrivelser av Noark 5, SIARD-referanser, DIAS, PREMIS, jobber, CLI og kjørebackend skal ikke skrives om bare fordi Data Workflow Manager-retningen er etablert.
