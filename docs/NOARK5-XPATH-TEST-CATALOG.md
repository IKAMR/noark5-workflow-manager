# Noark 5 XPath-testkatalog 2026

Fra z19.2 er mastergrunnlaget `IKAMR/KDRS_Query/doc/xml-queries_noark5_2026-05-26.txt` modellert som en JSON-katalog. Hver legacy-jobb har stabil intern test-ID, original `job_id`, testpunkt, `job_enabled`, kilde-XML, subsystem, Noark-versjonsmerking, tags, scope og en strukturert kjøredefinisjon.

Kjøring produserer ikke rapport. Den lager et immutable resultatsett under `Arbeid – operasjoner/noark5_tests/xpath/<timestamp>/` med `definitions.json`, `index.json` og én JSON-fil per test. Også legacy-deaktiverte tester får isolert resultatstatus når `include_disabled=True`; de kjøres ikke. Manglende `loependeJournal.xml`, `offentligJournal.xml` eller `endringslogg.xml` gir `source_missing`, ikke feil på hele kjøringen.

U1 og U2 er beholdt som egne aggregate-view tester. U1 bruker den allerede implementerte samlelogikken. U2 materialiserer én strukturert resultatblokk per arkivdel. Rapportering og sammensetting kommer senere.

Noark-versjon: masterfilen deklarerer 3.1, 4.0 og 5.0. Der `subsystem` er angitt i originalen bevares det eksplisitt. Øvrige tester er merket `master_query_subtype_needs_qa` inntil versjonsgyldighet er kvalitetssikret test for test.
