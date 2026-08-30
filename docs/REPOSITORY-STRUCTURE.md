# Repositorystruktur

## Root-prinsipp

Repo-root skal bare inneholde filer og mapper med en tydelig toppnivårolle: entrypoint, installasjon, oppstart, testing, avhengigheter, lisens, toppnivådokumentasjon og etablerte hovedmapper.

Generell applikasjonskode som ikke er GUI og ikke er Noark 5-spesifikk legges under `app/`. Generell konfigurasjon og policy legges under `config/`.

`noark5_workflow/` skal kun inneholde funksjonalitet og data som er spesifikt knyttet til Noark 5-domenet.

## Nåværende opprydding

- `settings_portable.py` flyttes fra root til `app/settings_portable.py`.
- `config_example.json` flyttes fra root til `config/config_example.json`.
- generell operasjonsmetadata etableres i `config/operations.json`.

`settings.py` og `version.py` beholdes foreløpig i root fordi de er sentrale importpunkter. Eventuell flytting gjøres senere som en samlet refaktorering.
