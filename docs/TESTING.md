# Testing

## Praktisk test av kontrollpunkt/resume

Praktisk test av `stopp -> avslutt program -> start program -> fortsett` krever minst to operasjoner i samme workflow.

Med bare én operasjon finnes det ikke et meningsfullt kontrollpunkt etter operasjonen, fordi workflow allerede er ferdig. Inntil minst to reelle operasjoner er tilgjengelige, dekkes checkpoint-modellen av automatiserte tester.

Når minst to operasjoner finnes, skal praktisk test minst dekke:

1. legg inn to operasjoner
2. sett `Stopp etter` på operasjon 1
3. kjør til status `Venter ved kontrollpunkt`
4. lagre og avslutt programmet
5. start programmet på nytt og åpne jobben
6. kontroller at `Fortsett workflow` vises
7. fortsett og kontroller at operasjon 2 kjøres uten at operasjon 1 kjøres på nytt
