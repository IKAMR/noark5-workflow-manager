# A15-regler som skal innarbeides i DEVELOPMENT.md

Disse reglene gjelder fra a15 og skal beholdes ved neste konsolidering av `DEVELOPMENT.md`.

1. Før en kodepakke leveres skal eksisterende regresjonstester kryssjekkes mot alle bevisste kontraktendringer. Kontroller minst versjon, registrerte operasjoner, fil-/mappestier og brukerrettede tekster. Kjør hele testsuiten når miljøet tillater det.
2. Ved start og avslutning av et increment skal det vurderes om nye erfaringer er kandidater til generell metodikk. Relevante kandidater registreres i `METHOD-OBSERVATIONS.md` uten at brukeren må be særskilt om det.
3. Profil er en eksplisitt grense: uten valgt profil skal GUI og Source være generiske. Formatspesifikk gjenkjenning og formatspesifikke operasjoner aktiveres av valgt profil.
