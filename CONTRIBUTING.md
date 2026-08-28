# Contributing

Takk for interesse for Noark 5 Workflow Manager.

## Issues

Bruk repositoryets Issue Forms for feil og forbedringsforslag. Søk først etter eksisterende saker.

Ikke publiser sensitivt arkivmateriale, personopplysninger, passord, interne stier eller andre opplysninger som ikke bør være offentlige.

## Bug reports

Oppgi minst:
- programversjon
- operativsystem
- funksjon/arbeidsoperasjon
- forventet og faktisk resultat
- trinn for å gjenskape feilen
- relevant loggutdrag, renset for sensitiv informasjon

## Feature requests

Beskriv behovet før løsningen. Oppgi gjerne om funksjonen er Noark 5-spesifikk eller kan være generisk og relevant for SIARD Workflow Manager.

Generisk funksjonalitet bør følge prinsippene i `docs/SHARED-DEVELOPMENT.md` og registreres i `docs/SHARED-ROADMAP.md` når den er relevant for begge kodebaser.

## Development

Les først:
1. `docs/DEVELOPMENT.md`
2. `docs/SHARED-DEVELOPMENT.md` for generisk funksjonalitet
3. `docs/ARCHITECTURE.md`
4. `docs/INTERFACE.md`
5. `docs/TESTING.md`

Gjør minst mulig nødvendig endring og unngå å omskrive større GUI- eller kjernelag uten behov.

Mottatte Noark 5-uttrekk skal i utgangspunktet behandles som bevaringsdokumentasjon. Genererte logger, rapporter og PREMIS skal ikke skrives inn i originaluttrekket.

## Testing

Kjør prosjektets `test.bat` etter meningsfulle kodeendringer og før commit. Gjør i tillegg relevant praktisk test via `start.bat`.

Nye funksjoner bør få automatiserte tester der det er praktisk mulig.

## Pull requests

Hold en pull request avgrenset til én logisk endring. Beskriv:
- hva som er endret
- hvorfor
- hvordan det er testet
- eventuell påvirkning på dokumenterte grensesnitt eller felles funksjonalitet med SIARD Workflow Manager

Knytt PR til relevant issue når det finnes, for eksempel `Fixes #27`.

## Commits and branches

Bruk korte, beskrivende commits. Feature-/bugfix-arbeid kan gjøres på egne branches før det foreslås inn i hovedgrenen eller tilbakeføres mellom Workflow Manager-prosjektene.
