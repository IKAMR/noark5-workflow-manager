# Testing

Noark 5 Workflow Manager bruker automatiserte tester, manuell GUI-/workflow-testing og senere validering mot kjente Noark 5-uttrekk.

## Normal testprosedyre

På Windows:

1. Kjør `install.bat` når avhengigheter er nye eller endret.
2. Kjør `test.bat`.
3. Kontroller at alle automatiserte tester består.
4. Start programmet med `start.bat`.
5. Gjennomfør relevante manuelle tester av GUI, workflow og faktiske uttrekk/pakker.
6. Commit først når testresultatet er tilfredsstillende.

## Automatiske testresultater

`test.bat` kjører alle `test_*.py` under `tests/` og lager automatisk en versjonert rapport:

```text
docs/test-results/v<VERSION>.md
```

Rapporten inneholder dato/tid, PASS/FAIL, antall tester og full testutskrift. Ny kjøring av samme versjon erstatter rapporten; det er sluttresultatet for den aktuelle versjonen som skal bevares.

## PREMIS-tester

a10 legger til `tests/test_premis_provenance.py`. Testene skal minst verifisere:

- PREMIS-fil med ett Noark 5-object, event(s) og Noark 5 Workflow Manager-agent
- gyldig DIAS_PREMIS `eventType` og fallback til `Adjustment`
- sentral registrering via `LocalExecutor`
- at loggeren kan slås av med `enable_premis_provenance`
- at PREMIS ikke erstatter vanlig workflow-logg

Når flere relevante operasjoner introduseres, skal tester kontrollere at de deklarerer riktig eventType og at read-only steg ikke feilaktig beskrives som innholdsendringer.

## Manuelle testresultater

Manuelle tester dokumenteres separat under `docs/manual-test-results/`, normalt én fil per versjon.

## Videre validering

Når analysefunksjoner for U1/U2, arkivstruktur og dokumentkontroll implementeres, skal resultater valideres mot kjente uttrekk og der det er relevant sammenlignes med eksisterende KDRS Query-resultater.

## Test av utdataisolasjon

Automatiske tester skal verifisere at workflow-PREMIS ikke skrives i eller ved siden av kildeområdet når ingen eksplisitt utdatamappe finnes, og at DIAS-pakking legger workflow-PREMIS i valgt DIAS-utdatamappe. Praktisk test bør også kontrollere at kildekatalogen er uendret etter workflow-kjøring.
