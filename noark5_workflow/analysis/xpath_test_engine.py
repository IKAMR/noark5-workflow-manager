from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
from statistics import mean
from typing import Any

from lxml import etree

from .u1_total import run_u1_total


def load_catalog(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _normalise_tree(path: Path) -> etree._ElementTree:
    parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)
    source = etree.parse(str(path), parser)
    root = deepcopy(source.getroot())
    for node in root.iter():
        if not isinstance(node.tag, str):
            continue
        node.tag = etree.QName(node).localname
        attrs = {}
        for key, value in node.attrib.items():
            local = etree.QName(key).localname if key.startswith("{") else key
            attrs["type" if local == "type" else local] = value
        node.attrib.clear()
        node.attrib.update(attrs)
    etree.cleanup_namespaces(root)
    return etree.ElementTree(root)


def _scalar(value: Any) -> Any:
    if isinstance(value, list):
        return [_scalar(v) for v in value]
    if isinstance(value, etree._Element):
        return "".join(value.itertext()).strip()
    if isinstance(value, etree._ElementUnicodeResult):
        return str(value).strip()
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _xpath(tree_or_node, expression: str) -> Any:
    return _scalar(tree_or_node.xpath(expression))


def _texts(node, select: str) -> list[str]:
    values = node.xpath(select)
    out=[]
    for value in values:
        text = _scalar(value)
        if isinstance(text, list):
            out.extend(str(x).strip() for x in text if str(x).strip())
        elif text is not None and str(text).strip():
            out.append(str(text).strip())
    return out


def _year_counts(node, select: str) -> dict[str, int]:
    counts=Counter()
    for text in _texts(node, select):
        if len(text)>=4: counts[text[:4]] += 1
    return dict(sorted(counts.items()))


def _date_range(node, select: str) -> dict[str, str | None]:
    values=[]
    for text in _texts(node, select):
        if len(text)>=10: values.append(text[:10])
    values.sort()
    return {'first':values[0] if values else None,'last':values[-1] if values else None}


def _group(node, spec: dict[str, Any]) -> dict[str, int]:
    counts=Counter()
    for item in node.xpath(spec['select']):
        if spec['type']=='group_attr':
            value=item.xpath('string('+spec.get('value','@type')+')') if isinstance(item, etree._Element) else ''
        elif spec['type']=='group_xpath':
            value=item.xpath('string('+spec.get('value','string(.)')+')') if isinstance(item, etree._Element) else ''
        else:
            value=_scalar(item)
        value=str(value or '').strip()
        if value: counts[value]+=1
    return dict(sorted(counts.items(), key=lambda x:x[0].casefold()))


def _eval_metrics(node, metrics: list[dict[str, Any]]) -> dict[str, Any]:
    result={}
    for spec in metrics:
        typ=spec.get('type','xpath')
        if typ=='xpath': result[spec['id']] = _xpath(node,spec['expression'])
        elif typ in {'group_text','group_attr','group_xpath'}: result[spec['id']] = _group(node,spec)
        elif typ=='year_counts': result[spec['id']] = _year_counts(node,spec['select'])
        elif typ=='date_range': result[spec['id']] = _date_range(node,spec['select'])
        else: raise ValueError(f"Ukjent metrikk-type: {typ}")
    return result


def _archive_parts(tree): return tree.xpath('//arkivdel')

def _part_identity(part, index):
    def tx(name): return str(part.xpath(f'string({name})') or '').strip()
    return {'index':index,'system_id':tx('systemID'),'title':tx('tittel'),'status':tx('arkivdelstatus')}


def _per_parts(tree, metrics):
    rows=[]
    for index, part in enumerate(_archive_parts(tree),1):
        rows.append({'archive_part':_part_identity(part,index),'values':_eval_metrics(part,metrics)})
    return rows


def _special(tree, test: dict[str, Any], source_path: Path):
    kind=test['execution']['kind']
    if kind=='u1_total':
        return run_u1_total(source_path)
    if kind=='u2_archive_parts':
        metrics=[
          {'id':'folder_count','type':'xpath','expression':'count(.//mappe)'},
          {'id':'registration_count','type':'xpath','expression':'count(.//registrering)'},
          {'id':'document_description_count','type':'xpath','expression':'count(.//dokumentbeskrivelse)'},
          {'id':'document_object_count','type':'xpath','expression':'count(.//dokumentobjekt)'},
          {'id':'classification_system_count','type':'xpath','expression':'count(.//klassifikasjonssystem)'},
          {'id':'class_count','type':'xpath','expression':'count(.//klasse)'},
          {'id':'folder_type_counts','type':'group_attr','select':'.//mappe','value':'@type'},
          {'id':'folder_status_counts','type':'group_text','select':'.//mappe/saksstatus'},
          {'id':'journalpost_type_counts','type':'group_text','select':'.//registrering/journalposttype'},
          {'id':'journal_status_counts','type':'group_text','select':'.//registrering/journalstatus'},
          {'id':'document_status_counts','type':'group_text','select':'.//dokumentbeskrivelse/dokumentstatus'},
          {'id':'document_medium_counts','type':'group_text','select':'.//dokumentbeskrivelse/dokumentmedium'},
          {'id':'variant_format_counts','type':'group_text','select':'.//dokumentobjekt/variantformat'},
          {'id':'correspondence_party_count','type':'xpath','expression':'count(.//korrespondansepart)'},
          {'id':'sakspart_count','type':'xpath','expression':'count(.//sakspart)'},
          {'id':'part_count','type':'xpath','expression':'count(.//part)'},
          {'id':'writeoff_count','type':'xpath','expression':'count(.//avskrivningsmaate)'},
          {'id':'screening_count','type':'xpath','expression':'count(.//skjerming)'},
          {'id':'disposal_count','type':'xpath','expression':'count(.//kassasjon)'},
          {'id':'performed_disposal_count','type':'xpath','expression':'count(.//utfoertKassasjon)'},
          {'id':'deletion_count','type':'xpath','expression':'count(.//sletting)'},
        ]
        return {'archive_parts':_per_parts(tree,metrics)}
    if kind=='classification_per_archive_part':
        return {'archive_parts':_per_parts(tree,[{'id':'classification_system_count','type':'xpath','expression':'count(.//klassifikasjonssystem)'},{'id':'class_count','type':'xpath','expression':'count(.//klasse)'},{'id':'folder_count','type':'xpath','expression':'count(.//mappe)'},{'id':'document_description_count','type':'xpath','expression':'count(.//dokumentbeskrivelse)'},{'id':'document_object_count','type':'xpath','expression':'count(.//dokumentobjekt)'},{'id':'part_count','type':'xpath','expression':'count(.//part)'}])}
    if kind in {'year_per_archive_part','registration_created_year_per_archive_part','registration_journal_year_per_archive_part'}:
        select={
          'year_per_archive_part':'.//mappe/opprettetDato',
          'registration_created_year_per_archive_part':'.//registrering/opprettetDato',
          'registration_journal_year_per_archive_part':'.//registrering/journaldato',
        }[kind]
        return {'archive_parts':_per_parts(tree,[{'id':'per_year','type':'year_counts','select':select}])}
    if kind=='class_folder_conflict_per_archive_part':
        return {'archive_parts':_per_parts(tree,[{'id':'class_with_subclass_and_folder','type':'xpath','expression':'count(.//klasse[klasse]/mappe)'}])}
    if kind=='folder_status_per_archive_part':
        return {'archive_parts':_per_parts(tree,[{'id':'folder_count','type':'xpath','expression':'count(.//mappe)'},{'id':'status_counts','type':'group_text','select':'.//mappe/saksstatus'},{'id':'meeting_folder_count','type':'xpath','expression':'count(.//mappe[@type="moetemappe"])'}])}
    if kind=='journalpost_type_per_archive_part':
        return {'archive_parts':_per_parts(tree,[{'id':'journalpost_type_counts','type':'group_text','select':'.//registrering/journalposttype'}])}
    if kind=='class_folder_list':
        rows=[]
        for cls in tree.xpath('//klasse[mappe]'):
            rows.append({'class_id':cls.xpath('string(klasseID)'),'title':cls.xpath('string(tittel)'),'folder_count':int(cls.xpath('count(mappe)'))})
        return {'classes':rows}
    if kind=='empty_class_list':
        return {'classes':[{'class_id':c.xpath('string(klasseID)'),'title':c.xpath('string(tittel)')} for c in tree.xpath('//klasse[not(klasse or mappe)]')]}
    if kind=='class_registration_conflict_list':
        return {'registrations':[{'class_id':r.xpath('string(../../klasseID)'),'system_id':r.xpath('string(systemID)')} for r in tree.xpath('//klasse[klasse]/registrering')]}
    if kind=='class_registration_list':
        rows=[]
        for cls in tree.xpath('//klasse[registrering]'):
            rows.append({'class_id':cls.xpath('string(klasseID)'),'title':cls.xpath('string(tittel)'),'registration_count':int(cls.xpath('count(registrering)'))})
        return {'classes':rows}
    if kind=='empty_class_per_archive_part':
        return {'archive_parts':_per_parts(tree,[{'id':'empty_class_count','type':'xpath','expression':'count(.//klasse[not(klasse or mappe or registrering)])'}])}
    raise ValueError(f"Ukjent spesial-handler: {kind}")


def run_test(test: dict[str, Any], extraction_root: str | Path) -> dict[str, Any]:
    extraction_root=Path(extraction_root)
    result={'result_format_version':1,'test_id':test['test_id'],'definition':test,'status':'not_run','source_xml':test['source_xml']}
    if test['legacy']['job_enabled']==0:
        result['status']='disabled_by_legacy_source'; return result
    source=extraction_root/test['source_xml']
    if not source.is_file():
        result['status']='source_missing'; result['source_path']=str(source); return result
    try:
        tree=_normalise_tree(source)
        kind=test['execution']['kind']
        values=_eval_metrics(tree,test['execution'].get('metrics',[])) if kind=='metrics' else _special(tree,test,source)
        result.update({'status':'ok','source_path':str(source),'values':values})
    except Exception as exc:
        result.update({'status':'error','source_path':str(source),'error':f'{type(exc).__name__}: {exc}'})
    return result


def run_catalog(catalog_path: str | Path, extraction_root: str | Path, output_dir: str | Path, *, include_disabled: bool=True) -> dict[str, Any]:
    catalog=load_catalog(catalog_path)
    output_dir=Path(output_dir); results_dir=output_dir/'results'; results_dir.mkdir(parents=True,exist_ok=True)
    snapshot=output_dir/'definitions.json'; snapshot.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    index={'result_set_format_version':1,'catalog_id':catalog['catalog_id'],'source_master':catalog['source'],'extraction_root':str(Path(extraction_root)),'tests':[]}
    for test in catalog['tests']:
        if not include_disabled and test['legacy']['job_enabled']==0: continue
        result=run_test(test,extraction_root)
        filename=test['test_id'].replace('.','_')+'.json'
        (results_dir/filename).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        index['tests'].append({'test_id':test['test_id'],'legacy_job_id':test['legacy']['job_id'],'test_point':test['legacy']['test_point'],'status':result['status'],'file':'results/'+filename})
    index['summary']={k:sum(1 for r in index['tests'] if r['status']==k) for k in sorted({r['status'] for r in index['tests']})}
    (output_dir/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return index
