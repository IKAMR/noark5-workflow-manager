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

Ved overlay/reparasjonspakke skal appen lukkes før filene legges over repository.

## Automatiske testresultater

`test.bat` kjører alle `test_*.py` under `tests/` og lager automatisk en versjonert rapport:

```text
docs/test-results/v<VERSION>.md
```

Rapporten inneholder dato/tid, PASS/FAIL, antall tester og full testutskrift. Ny kjøring av samme versjon erstatter rapporten; det er sluttresultatet for den aktuelle versjonen som skal bevares.

## PREMIS-tester

Testene skal minst verifisere:

- PREMIS-fil med ett Noark 5-object, event(s) og Noark 5 Workflow Manager-agent
- gyldig DIAS_PREMIS `eventType` og fallback til `Adjustment`
- sentral registrering via `LocalExecutor`
- at loggeren kan slås av med `enable_premis_provenance`
- at PREMIS ikke erstatter vanlig workflow-logg
- at PREMIS-historikk bevares ved gjentatt kjøring
- at workflow-PREMIS ikke skrives i eller ved siden av kildeområdet uten eksplisitt utdata

Når flere relevante operasjoner introduseres, skal tester kontrollere at de deklarerer riktig eventType og at read-only steg ikke feilaktig beskrives som innholdsendringer.

## Manuelle testresultater

Manuelle tester dokumenteres separat under `docs/manual-test-results/`, normalt én fil per versjon når dette er relevant.

## Videre validering

Når analysefunksjoner for U1/U2, arkivstruktur og dokumentkontroll implementeres, skal resultater valideres mot kjente uttrekk og der det er relevant sammenlignes med eksisterende KDRS Query-resultater.

## Test av utdataisolasjon

Automatiske tester skal verifisere at workflow-PREMIS ikke skrives i eller ved siden av kildeområdet når ingen eksplisitt utdatamappe finnes, og at DIAS-pakking legger workflow-PREMIS i valgt DIAS-utdatamappe. Praktisk test bør også kontrollere at kildekatalogen er uendret etter workflow-kjøring.

## Praktisk regresjonstest

- Test single-jobb og `Start alle` med separate outputområder.
- Kontroller at samme source kan brukes i flere jobber uten at output eller parametre lekker mellom jobbene.
- Kontroller redigering og kontrollert ny kjøring av tidligere jobb.
- Kontroller at aktiv jobb er synlig i hovedvindu og Jobber-vindu.
- Kontroller at PREMIS-historikk bevares ved gjentatt kjøring mot samme jobbs outputområde.
- Kontroller at overordnet run-logg opprettes både for single og batch.
- Kontroller at batchfase og feil blir synlige dersom batch stopper før første jobb starter.
- Kontroller fallback og `Bruk standard` for `logs/runs`, `setup` og `joblists`.
- Praktisk kontrollpunkt stop/fortsett kan først fulltestes når minst to reelle operasjoner finnes i samme workflow.
- Crash-recovery for ulagrede jobblisteendringer er ikke implementert ennå; dette står i `TODO-ROADMAP.md`.

### Praktisk kontroll av eksplisitt fortsettelse (v0.1.2-a11)

Når en testjobb har minst to operasjoner og et aktivt kontrollpunkt (`■`) etter en operasjon før siste steg:

1. Kjør valgt jobb til kontrollpunktet i GUI eller med `n5wf jobs run <file.n5jobs> --job <job-id>`.
2. Kontroller med `n5wf jobs status <file.n5jobs> --job <job-id>` at jobben står `Venter ved kontrollpunkt` og at neste operasjon er bevart.
3. Fortsett med GUI-handlingen `Fortsett workflow` og kontroller at ferdige operasjoner ikke kjøres på nytt.
4. Gjenta fra et kontrollpunkt og bruk `n5wf jobs continue <file.n5jobs> --job <job-id>`; forvent exit code `0` når jobben fullføres, eller `5` dersom et nytt kontrollpunkt nås.
5. Forsøk `continue` på en jobb som ikke venter ved kontrollpunkt; forvent exit code `3` og at jobben ikke kjøres.
6. Forsøk med ukjent jobb-ID; forvent exit code `6`.
7. Kontroller at andre jobber i samme `.n5jobs`-fil er uendret.

## Planlagte testområder

Videre utvikling skal ha automatiserte tester for:

- transfer A->B og checksum-likhet
- feil ved avvik mellom kilde og destinasjon
- ingen skriving til read-only kilde
- korrekt PREMIS for transfer/verifikasjon
- Arkade CLI-adapter med kontrollert fake/stub der praktisk
- native Noark-kontroller mot kjente XPath/KDRS Query-resultater
- recursive discovery/prequalification/skip/retry
- store kandidater uten utilsiktet full kopiering eller hashing i discovery-steget
- final AIP/AIC-selection slik at debug-/arbeidsmateriale ikke inkluderes uten eksplisitt valg
