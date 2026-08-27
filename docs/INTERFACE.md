# Grensesnitt og kontrakter

Dette dokumentet beskriver stabile grensesnitt som andre deler av Noark 5 Workflow Manager skal kunne bygge på.

## Operasjoner

Operasjoner registreres i `OperationRegistry`, mottar en `OperationContext` og returnerer et `OperationResult`. GUI skal ikke omgå executorlaget for å kjøre operasjoner direkte.

## Workflow

Workflow-modellen eier rekkefølgen på valgte operasjoner. GUI-komponentene presenterer denne tilstanden, men skal ikke være eneste lagringssted for den.

## DIAS-pakking

DIAS-dialogen produserer parametere til DIAS-operasjonen. Valgt Noark 5-uttrekk er kildeinnhold. Manuelt lagt til filer og mapper er tilleggsinnhold i den genererte pakken og skal ikke skrives tilbake til kildemappen på disk.
