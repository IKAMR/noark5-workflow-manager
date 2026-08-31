# Kjøremiljø og plattformstøtte

Dette dokumentet er autoritativt for hvilke kjøremiljøer Noark 5 Workflow Manager faktisk støtter i dag, hvilke miljøer som er teknisk mulige, og hvilke plattformbindinger som må håndteres videre.

## Status nå

### Testet og støttet

Dagens utviklings- og testbaseline er **Windows desktop**.

Normal prosedyre er:

1. `install.bat` når avhengigheter er nye eller endret.
2. `test.bat`.
3. Kontroller at testene består.
4. `start.bat`.
5. Praktisk test av relevante GUI-/workflow-funksjoner.

At Python-kjernen kan være portabel betyr ikke at et annet operativsystem regnes som støttet før installasjon, oppstart og testregime er etablert og praktisk verifisert der.

Planlagt lokal CLI/programmatisk styring er en arkitekturretning, men er ikke implementert eller en støttet brukerflate i dagens baseline.

## Plattformbindinger i dagens løsning

Selve applikasjonskjernen er i liten grad bundet til Windows.

I hovedsak plattformuavhengig:

- Python-kode og `pathlib`
- Noark 5-kildemodell
- XML-behandling
- TAR/pakking
- SHA-256 og annen filbasert kontroll
- DIAS-logikk
- Job/Batch-modell
- `.n5jobs`-format
- operations/executor-kontrakten
- `customtkinter`, `lxml` og `psutil` finnes for flere desktop-plattformer

Windows-spesifikt i dagens distribusjon:

- `install.bat`
- `start.bat`
- `test.bat`
- bruk av Windows `py` launcher i disse skriptene
- enkelte konvensjoner for bruker-/applikasjonsdata

`.bat`-filene skal betraktes som launchere og test-/installasjonshjelp, ikke som applikasjonslogikk. Ny core- eller operations-kode skal ikke gjøres Windows-avhengig uten et dokumentert behov.

## Brukerdata og arbeidsstatus

Runtime-data skal ikke være avhengig av Git-repository eller installasjonsmappen.

Automatisk arbeidsstatus/jobbliste skal lagres per bruker i et egnet application-data-område. På Windows brukes normalt et område under `%LOCALAPPDATA%`.

Målet for videre opprydding er én plattformuavhengig mekanisme, for eksempel `get_app_data_dir()`, som velger riktig plassering:

- Windows: `%LOCALAPPDATA%/...`
- Linux: XDG-kompatibelt brukerdataområde
- macOS: `~/Library/Application Support/...`

Brukerinnstillinger som i dag ligger i lokal `config.json` bør på sikt bruke samme prinsipp, særlig før flerbrukerdrift på Terminal Server/RDS.

En framtidig lokal SQLite-database for jobb-/arbeidsflytdata skal følge samme prinsipp og ligge i egnet applikasjonsdataområde, ikke i repository/installasjonsmappen. SQLite er foretrukket kandidat, men skjema er ikke låst.

## Lokal headless/CLI-kjøring

Planlagt CLI/programmatisk styring skal skilles fra framtidig remote server/worker.

En lokal CLI skal kunne bruke samme lokale jobb-/workflow-/`LocalExecutor`-lag uten at desktop-GUI-et er startet. Dette kan gi scriptbar og automatiserbar kjøring på en enkelt maskin uten at nettverksserver, autentisering eller remote worker er nødvendig.

CLI må få eget installasjons-/oppstarts-/testløp før den dokumenteres som støttet.

## Windows Server, RDS og Terminal Server

### GUI på Windows Server/RDS

Det finnes ingen kjent fundamental arkitekturhindring for å kjøre dagens desktop-GUI i et Windows Server/RDS-/Terminal Server-miljø.

Før dette erklæres som støttet bør følgende testes:

- installasjon og oppstart per/felles installasjon
- Tk/CustomTkinter i RDS-sesjon
- per-user config og autosave
- tilgang til lokale og delte lagringsområder
- UNC-/nettverksstier der de brukes
- samtidige brukere
- output/resource locking mellom appinstanser
- filrettigheter og lange stier
- praktisk kjøring av representative Noark 5-jobber

Citrix, Azure Virtual Desktop og VMware Horizon ligger konseptuelt nær samme modell når programmet faktisk kjører i et Windows-brukermiljø.

### Headless server/worker

Dagens program har `LocalExecutor`. Arkitekturen har en eksplisitt grense for senere `RemoteExecutor`, men en komplett headless workflow-server/worker er **ikke implementert**.

En framtidig serverløsning må blant annet håndtere:

- API/protokoll mellom klient og server
- autentisering og autorisasjon
- TLS
- varig jobbkø
- worker-prosesser
- status og fremdrift
- stopp, retry og senere resume/checkpoints
- mapping av lagringsreferanser
- revisjonslogging
- isolasjon av filstier og samtidige jobber

For store arkivuttrekk skal klienten normalt sende jobbreferanser og stabile lagringsreferanser, ikke laste hele uttrekket gjennom GUI/API.

Den framtidige server-/API-modellen bør gjenbruke samme jobb-/kommandomodell som lokal GUI/CLI der det er praktisk, men lokal CLI er ikke avhengig av at serverdelen først implementeres.

## Linux

Linux desktop vurderes som realistisk uten redesign av core.

Det som minst må etableres og testes:

- `install.sh`
- `start.sh`
- `test.sh`
- bruk av `python3`
- tilgjengelig Tk/Tcl i operativsystemet
- installasjon av Python-avhengigheter
- case-sensitive filsystem
- filrettigheter
- application-data-path
- mountede nettverks-/lagringsområder
- eksterne verktøy og deres executable paths

Linux skal ikke beskrives som støttet før denne kjeden er praktisk testet.

Linux er også en naturlig kandidat for framtidig lokal CLI, headless worker/server og containerisert backend.

## macOS

macOS desktop vurderes også som realistisk, men er ikke dagens testede plattform.

Det må blant annet etableres/testes:

- `python3` og riktig Tcl/Tk
- install/start/test-skript eller pakket `.app`
- application data under `~/Library/Application Support/...`
- filstier og rettigheter
- packaging, signering/notarization dersom programmet distribueres som vanlig macOS-applikasjon
- eksterne verktøy

En framtidig CLI kan i prinsippet være enklere å portere enn desktop-GUI-et, men skal ikke omtales som støttet på macOS før den er testet der.

## Android og andre mobile plattformer

Dagens Tk/CustomTkinter-GUI er ikke et naturlig Android-grensesnitt.

Core-logikk kan i prinsippet gjenbrukes, men en native mobilklient ville kreve et annet GUI-lag. For arkivarbeid med store uttrekk er en bedre langsiktig modell normalt:

```text
Android / iPad / annen klient
            |
            v
         Web/API
            |
            v
      Workflow Server
            |
            v
          Worker
```

Mobilen blir da kontroll-/statusklient og behandler ikke store Noark 5-uttrekk lokalt.

## Webklient

En framtidig webklient kan gi ett brukergrensesnitt for:

- Windows
- Linux
- macOS
- Android
- iPadOS
- Chromebook og andre nettleserplattformer

Webklient forutsetter server/API og er derfor et senere lag, ikke en erstatning for dagens lokale desktop-GUI nå.

## Container / Docker / Podman

Containerisering vurderes som mest relevant for framtidig backend/worker, særlig på Linux.

Desktop-GUI skal ikke containeriseres bare for å oppnå portabilitet. Core, operations og headless worker er de naturlige containergrensene. En framtidig CLI kan også være relevant i container-/headless-sammenheng.

## Pakket Windows-applikasjon

En framtidig Windows-pakke/executable kan gjøre at sluttbrukere ikke trenger egen Python-installasjon eller å forholde seg til `install.bat`.

Dette endrer distribusjonen, ikke operations/executor-arkitekturen.

## Utviklingsregler for portabilitet

Ved ny utvikling skal vi:

1. unngå nye hardkodede Windows-stier
2. bruke `pathlib` og plattformuavhengige Python-API-er når mulig
3. holde `.bat`, `.sh` og eventuell packaging utenfor domenelogikken
4. holde core/operations uavhengig av GUI
5. holde jobb-/workflowfunksjoner i et delt lag som kan brukes av GUI, CLI og senere API
6. kapsle eksterne programmer i adaptere med konfigurerbar executable/path
7. lagre runtime-state og brukerinnstillinger utenfor source repository/installasjonsmappe
8. bevare operations/executor-kontrakten slik at lokal og senere remote kjøring kan bruke samme operasjoner
9. teste et miljø eller grensesnitt før dokumentasjonen kaller det støttet

## Prioritert retning

En naturlig utviklingsrekkefølge er:

1. Windows desktop
2. lokal CLI/programmatisk styring når jobb-/workflowlaget er klart for det
3. Windows RDS/Terminal Server
4. headless worker/server på Windows og/eller Linux
5. webklient
6. Linux/macOS desktop dersom behovet tilsier det
7. native mobilklient bare dersom webklient ikke dekker behovet

Se også `ARCHITECTURE.md` for kjørebackend og servermodell, `INTERFACE.md` for planlagte grensesnitt og `TESTING.md` for dagens testregime.
