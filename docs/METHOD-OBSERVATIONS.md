# Metodikkobservasjoner

Dette dokumentet samler erfaringer fra utviklingen av Noark 5 Workflow Manager som kan være relevante for det separate repositoriet `IKAMR/incremental-ai-development-method`.

Observasjonene her er **ikke metodikkvedtak**. De er kandidater som skal vurderes samlet i egne metodikketapper. Løpende prosjektutvikling skal derfor ikke automatisk føre til endringer i metodikk-repositoriet.

## Arbeidsregel

Når utviklingen avdekker en mulig generell metodikkforbedring:

1. Registrer observasjonen kort i dette dokumentet.
2. Ikke endre metodikk-repositoriet som en automatisk del av prosjektendringen.
3. Fortsett prosjektutviklingen dersom observasjonen ikke påvirker gjeldende increment.
4. Vurder flere observasjoner samlet i en senere metodikkrunde.
5. Klassifiser da hvert punkt som:
   - overføres til metodikken
   - slås sammen med andre observasjoner
   - beholdes som prosjektspesifikt
   - forkastes
6. Når et punkt er behandlet, flyttes det fra `Åpne observasjoner` til `Behandlede observasjoner` med resultat og eventuell referanse.

## Avgrensning mot teknisk gjeld

Dette dokumentet skal ikke brukes som vanlig feil- eller oppgaveliste for Noark 5 Workflow Manager.

- Prosjektspesifikke feil, begrensninger og teknisk gjeld hører hjemme i prosjektets ordinære oppfølgingsmekanisme.
- `METHOD-OBSERVATIONS.md` brukes bare når erfaringen kan ha generell verdi for AI-assistert utviklingsmetodikk.
- Samme hendelse kan gi både et prosjektspesifikt tiltak og en metodikkobservasjon, men de skal behandles som to forskjellige forhold.

---

## Åpne observasjoner

### MO-001 – Ikke-blokkerende tekniske funn må ikke forsvinne

**Oppstått:** v0.1.2-a13

**Bakgrunn:**  
Under test av a13 ble det observert en `lxml.etree`/Python GIL-advarsel samtidig som hele testsuiten bestod. Funnet var dermed ikke blokkerende, men var konkret og relevant for kjøremiljøet.

**Observasjon:**  
Et lite teknisk funn kan lett bli omtalt i samtalen og deretter forsvinne når utviklingen fortsetter. Samtidig er det uheldig dersom hvert slikt funn automatisk utvider aktivt scope.

**Mulig generell læring:**  
Metodikken bør ha en eksplisitt mekanisme der et konkret ikke-blokkerende funn enten:

1. prioriteres og håndteres i aktivt increment, eller
2. registreres varig i prosjektets eksisterende issue-/technical-debt-/known-issues-mekanisme for senere prioritering.

Dette kombinerer sporbarhet med scope-disiplin.

**Metodikkstatus:** Til senere samlet vurdering.

### MO-002 – Metodikkforbedringer bør samles før overføring til metodikk-repositoriet

**Oppstått:** v0.1.2-a13

**Bakgrunn:**  
En enkelt utviklingserfaring utløste først forslag om umiddelbar endring i det separate metodikk-repositoriet. Det gir risiko for at generell metodikk endres for reaktivt ut fra enkelthendelser i ett prosjekt.

**Observasjon:**  
Prosjektarbeid gir løpende små erfaringer som kan være metodisk interessante. Verdien og generaliserbarheten blir lettere å vurdere når flere observasjoner sees i sammenheng.

**Mulig generell læring:**  
Prosjekter som bruker metodikken kan ha en lokal oppsamlingsfil for metodikkobservasjoner. Kandidatene vurderes samlet i egne metodikketapper før den overordnede metodikken endres.

En observasjon skal derfor ikke automatisk bli en metodikkregel.

**Metodikkstatus:** Til senere samlet vurdering.

---

## Behandlede observasjoner

Ingen foreløpig.

Ved senere metodikkgjennomgang bør behandlet punkt beholde ID og få dokumentert:

- beslutning
- begrunnelse
- eventuell sammenslåing med andre observasjoner
- hvor i metodikk-repositoriet endringen ble gjort
- issue-/commit-referanse når relevant
