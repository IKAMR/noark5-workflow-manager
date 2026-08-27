# Utviklingsregler

Før analyse eller endring av kode i dette repositoriet:

1. Les `docs/DEVELOPMENT.md`.
2. Les `docs/ARCHITECTURE.md` der den finnes og er relevant.
3. Les `docs/INTERFACE.md` ved endringer i grensesnitt eller kontrakter.
4. Les `docs/DEFINITIONS.md` ved endringer som berører begreper og lagdeling.
5. Behandle dokumentert arkitektur som målbildet. Kontroller samtidig den faktiske koden før endringer gjøres.

## Endringsprinsipp

- Bevar fungerende funksjonalitet og gjør den minste nødvendige endringen.
- Ikke erstatt et etablert GUI-panel i sin helhet bare for å legge til en kontroll eller funksjon.
- Noark 5-uttrekket og DIAS SIP/AIC er separate lag. DIAS-pakking kan supplere pakkens innhold og metadata uten å endre kildefilene på disk.
- Nye funksjoner skal ha automatiserte tester når det er praktisk mulig.
- Før commit av en alpha: kjør `test.bat`, deretter praktisk test via `start.bat`.

## Versjonering

Kildekoden bruker versjon som `0.1.0-a9`. Git-tag kan bruke `v0.1.0-a9`.
