# Jobs and batches

Introduced in v0.1.1-a1; first executable local batch scheduler in v0.1.1-a2.

## User-facing hierarchy

1. **Jobber** – oversikt over én eller flere jobber.
2. **Workflow** – detaljert arbeidsflate for én aktiv jobb.
3. **Resultater** – senere eget aggregert resultatnivå.

Scheduler og Worker er tekniske lag og skal normalt vises som status, ikke som egne hovedvinduer.

## Core model

```text
Batch
├── JOB-001 -> source A -> workflow A -> output A
├── JOB-002 -> source B -> workflow B -> output B
└── JOB-003 -> source C -> workflow C -> output C
```

Én Job eier sin egen kilde, workflow, operasjonsparametre, utdata, status og kjørelogg.

## Start alle – v0.1.1-a2

`Start alle` kjører alle jobber **sekvensielt** på `LocalExecutor` i den rekkefølgen de står i batchen.

- Jobber uten operasjoner markeres `Hoppet over`.
- Hver jobb får egen status, fremdrift, siste melding og intern kjørelogg.
- Hovedloggen viser batchhendelser med jobb-ID som prefiks.
- Batchoversikten viser samlet antall `Ferdig`, `Feil`, `Klar`, `Kjører` og `Hoppet over`.
- `Stopp` ber den aktive operasjonen stoppe ved neste avbruddspunkt og starter ikke nye jobber etterpå.
- Jobber og batch er fortsatt in-memory i a2. Det finnes ennå ingen lagre/gjenoppta-funksjon.

## Per-jobb konfigurasjon

Konfigurerbare operasjoner må ha parametre lagret på Job-objektet. Dette er kritisk for DIAS-pakking: JOB-001, JOB-002 osv. kan ha ulike utdataområder og metadata uten at siste åpne jobb overskriver de andre.

## Output/resource locking

Fra a2 opprettes en liten `.noark5-workflow-manager.lock` i eksplisitt valgt utdataområde mens jobben kjører. Dette hindrer to jobber eller to appinstanser i å skrive til samme utdataområde samtidig.

Ved normal avslutning fjernes låsen automatisk. Etter maskin-/prosesskrasj kan en lås bli liggende igjen; den skal ikke slettes automatisk uten kontroll fordi den kan representere en faktisk aktiv annen instans.

## Planned execution layers

```text
Workflow -> Job -> Batch -> Scheduler -> Worker
```

A2 implementerer en enkel lokal sekvensiell scheduler. Parallellitet, prioritet, retry, persistent kø og remote workers kommer senere.

## Design rules

- Recursive discovery skal opprette/prekvalifisere Jobs, ikke kjøre direkte i GUI-loop.
- Store objekter skal ikke kopieres, pakkes ut eller hashes bare fordi de oppdages.
- Original/received sources er i utgangspunktet read-only.
- Hver jobb skal ha isolert output/proveniens.
- Remote/server execution skal bruke job specifications og storage references fremfor å sende store payloads gjennom GUI-et.
