# v0.1.1-a2

Første kjørbare lokale batch-versjon.

## Nytt

- `Start alle` kjører alle jobber sekvensielt.
- `Stopp` stopper batchen ved neste avbruddspunkt og starter ikke nye jobber.
- DIAS-parametre og valgt utdata lagres separat per jobb i minnet.
- Jobboversikten viser kilde, utdata, status, fremdrift og siste melding.
- Per-jobb kjørelogg beholdes i minnet og vises når jobben åpnes.
- Samlet batchstatus vises i Jobber-vindu og kjørelogg.
- Output-lock hindrer parallelle appinstanser/jobber i å skrive til samme outputområde.
- Jobb/batch kan fortsatt ikke lagres og gjenopptas mellom appstarter; dette er bevisst ikke del av a2.
