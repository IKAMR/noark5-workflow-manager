from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path

from noark5_workflow.analysis.xpath_test_engine import run_catalog, run_test

ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'config/noark5/tests/xpath_catalog_2026_05_26.json'

class A21XpathCatalogQATests(unittest.TestCase):
    def setUp(self):
        self.catalog=json.loads(CAT.read_text(encoding='utf-8'))
        self.by={t['legacy']['job_id']:t for t in self.catalog['tests']}

    def test_archive_part_scopes(self):
        ids={'C05.01_R3','C09_R4','C10_R5','C13.01','C15.01','C16_R6','C16.01_R7'}
        for job_id in ids:
            self.assertEqual('archive_part',self.by[job_id]['scope'],job_id)

    def test_f13_preserves_legacy_and_normalizes_test_point(self):
        t=self.by['F13']
        self.assertIsNone(t['legacy']['test_point'])
        self.assertEqual('N5.47',t['normalized_test_point'])

    def test_l02_has_generic_parent_metrics(self):
        metrics={m['id']:m for m in self.by['L02']['execution']['metrics']}
        self.assertIn('registrering',metrics)
        self.assertIn('dokumentbeskrivelse',metrics)
        self.assertEqual('count(//registrering/virksomhetsspesifikkeMetadata)',metrics['registrering']['expression'])

    def test_i02_cross_file_match_and_mismatch(self):
        t=self.by['I02']
        self.assertEqual('cross_file_journal_date_comparison',t['execution']['kind'])
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'arkivstruktur.xml').write_text('<arkiv><registrering type="journalpost"><opprettetDato>2024-01-01T00:00:00</opprettetDato></registrering><registrering type="journalpost"><opprettetDato>2024-12-31T00:00:00</opprettetDato></registrering></arkiv>',encoding='utf-8')
            journal='<journal><journalregistrering><journalpost><journaldato>2024-01-01</journaldato></journalpost></journalregistrering><journalregistrering><journalpost><journaldato>2024-12-31</journaldato></journalpost></journalregistrering></journal>'
            (root/'loependeJournal.xml').write_text(journal,encoding='utf-8')
            (root/'offentligJournal.xml').write_text(journal,encoding='utf-8')
            result=run_test(t,root)
            self.assertEqual('ok',result['status'])
            self.assertEqual('match',result['values']['comparison']['status'])
            (root/'offentligJournal.xml').write_text('<journal><journalregistrering><journalpost><journaldato>2024-01-02</journaldato></journalpost></journalregistrering><journalregistrering><journalpost><journaldato>2024-12-31</journaldato></journalpost></journalregistrering></journal>',encoding='utf-8')
            result=run_test(t,root)
            self.assertEqual('mismatch',result['values']['comparison']['status'])

    def test_catalog_event_stream_is_flushed_per_test(self):
        mini={
            'catalog_id':'a21-mini',
            'source':{'role':'test'},
            'tests':[
                {'test_id':'mini.one','legacy':{'job_id':'X01','test_point':'N5.X','job_enabled':1},'name':'Mini','source_xml':'arkivstruktur.xml','scope':'source_document','execution':{'kind':'metrics','metrics':[{'id':'count','type':'xpath','expression':'count(//mappe)'}]},'status':'active','tags':[],'noark_versions':['5.0']}
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'src'; out=Path(tmp)/'out'; root.mkdir()
            (root/'arkivstruktur.xml').write_text('<arkiv><mappe/></arkiv>',encoding='utf-8')
            cat=Path(tmp)/'cat.json'; cat.write_text(json.dumps(mini),encoding='utf-8')
            events=[]
            run_catalog(cat,root,out,progress_callback=lambda *args: events.append(args))
            lines=[json.loads(x) for x in (out/'test-events.jsonl').read_text(encoding='utf-8').splitlines()]
            self.assertEqual(['test.started','test.finished'],[x['event'] for x in lines])
            self.assertIn('duration_seconds',lines[1])
            self.assertEqual(2,len(events))

if __name__=='__main__': unittest.main()
