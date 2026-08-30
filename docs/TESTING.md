# Testing


## Praktiske tester før v0.1.2-a2 låses

- Lukk hele appen før en reparasjonspakke legges over repoet; Python-moduler som allerede er lastet blir ellers ikke erstattet i kjørende prosess.
- Kjør alltid `test.bat` etter overlay og deretter `start.bat` for praktisk test.
- Test single-jobb og `Start alle` med separate outputområder.
- Kontroller at PREMIS-historikk bevares ved gjentatt kjøring mot samme jobbs outputområde.
- Kontroller at overordnet run-logg opprettes både for single og batch.
- Kontroller fallback og `Bruk standard` for `logs/runs`, `setup` og `joblists`.
- Praktisk kontrollpunkt stop/fortsett kan først fulltestes når minst to reelle operasjoner finnes i samme workflow.
- Crash-recovery for ulagrede jobblisteendringer er ikke implementert ennå; dette står i `TODO-ROADMAP.md`.
