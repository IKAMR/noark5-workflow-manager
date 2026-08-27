# v0.1.0 baseline

`v0.1.0` promotes the corrected `v0.1.0-a10.1` implementation to the first stable documented baseline. No new large runtime feature is introduced in the promotion itself.

## Included baseline

- Noark 5 source selection/detection and workflow GUI
- local executor boundary and future remote-executor direction
- DIAS package metadata dialog and package tree
- import of existing METS/info.xml metadata
- add file / add folder / create folder
- direct streaming of added folders into uncompressed TAR
- persistent last-used folders
- automated test-result documentation
- central workflow PREMIS adapted from SIARD Workflow Manager
- workflow PREMIS written only to explicitly selected work/output area

## Documentation baseline

This release adds a compact cross-project documentation layer so humans and AI can recover the intended architecture quickly:

- `DEVELOPMENT.md` – non-negotiable development rules
- `ARCHITECTURE.md` – implemented and target architecture
- `INTERFACE.md` – stable/current contracts
- `DEFINITIONS.md` – terminology
- `TESTING.md` – test regime
- `CODE-MAP.md` – code/dataflow map
- `SHARED-DEVELOPMENT.md` – interaction with SIARD Workflow Manager
- `SHARED-ROADMAP.md` – implemented/planned shared candidates

## Next development themes

The roadmap after v0.1.0 includes native Noark validation/reporting, Arkade 5 CLI integration, transfer/verify/PREMIS between storage zones, pipeline orchestration, recursive jobs/batch processing and explicit final AIP/AIC finalization.
