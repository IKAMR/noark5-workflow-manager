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

Eksempel:

```text
docs/test-results/v0.1.0-a7.md
```

Rapporten inneholder dato/tid, PASS/FAIL, antall tester og full testutskrift.

## Manuelle testresultater

Manuelle tester dokumenteres separat under:

```text
docs/manual-test-results/
```

Normalt brukes én fil per versjon:

```text
v0.1.0-a7.md
```

Ved flere større, avgrensede testforløp kan beskrivende suffiks brukes, for eksempel:

```text
v0.1.0-a7_dias-package.md
v0.1.0-a7_mets-import.md
```

## Videre validering

Når analysefunksjoner for U1/U2, arkivstruktur og dokumentkontroll implementeres, skal resultater valideres mot kjente uttrekk og der det er relevant sammenlignes med eksisterende KDRS Query-resultater.
