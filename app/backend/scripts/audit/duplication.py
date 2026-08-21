import sqlite3
import re
import hashlib
from typing import Dict, List
from .connection import rows

def _normalize_literal(text: str) -> str:
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip()

def _normalize_conservative(text: str) -> str:
    if not text: return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def _hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def check_duplication(db: sqlite3.Connection) -> dict:
    all_questions = rows(db, "SELECT id, institution_code, year, stem FROM questions")
    
    literal_groups: Dict[str, List[dict]] = {}
    normalized_groups: Dict[str, List[dict]] = {}
    
    for q in all_questions:
        st = q["stem"]
        if not st: continue
        
        lit = _normalize_literal(st)
        if lit:
            hl = _hash(lit)
            if hl not in literal_groups: literal_groups[hl] = []
            literal_groups[hl].append(q)
            
        norm = _normalize_conservative(st)
        if norm:
            hn = _hash(norm)
            if hn not in normalized_groups: normalized_groups[hn] = []
            normalized_groups[hn].append(q)
            
    def _categorize(groups, skip_ids=set()):
        same_inst_year = []
        cross_inst = []
        same_inst_diff_year = []
        other_mixed = []
        
        affected_count = 0
        new_skip = set()
        
        for h, qs in sorted(groups.items()):
            valid_qs = [q for q in qs if q["id"] not in skip_ids]
            if len(valid_qs) > 1:
                group_qs = [{"id": q["id"], "institution": q["institution_code"], "year": q["year"]} for q in sorted(valid_qs, key=lambda x: x["id"])]
                group = {
                    "hash": h,
                    "count": len(valid_qs),
                    "questions": group_qs
                }
                affected_count += len(valid_qs)
                new_skip.update([q["id"] for q in valid_qs])
                
                insts = set(q["institution_code"] for q in valid_qs)
                years = set(q["year"] for q in valid_qs)
                
                if len(insts) == 1 and len(years) == 1:
                    same_inst_year.append(group)
                elif len(insts) == 1 and len(years) > 1:
                    same_inst_diff_year.append(group)
                elif len(insts) > 1:
                    cross_inst.append(group)
                else:
                    other_mixed.append(group)
                    
        return {
            "affected_questions_count": affected_count,
            "groups_count": len(same_inst_year) + len(same_inst_diff_year) + len(cross_inst) + len(other_mixed),
            "same_institution_year": same_inst_year,
            "same_institution_different_year": same_inst_diff_year,
            "cross_institution": cross_inst,
            "other_mixed_group": other_mixed
        }, new_skip

    literal_res, literal_skip = _categorize(literal_groups)
    normalized_res, _ = _categorize(normalized_groups, literal_skip)
    
    return {
        "literal_exact": literal_res,
        "normalized_exact": normalized_res,
        "probable_duplicate": {
            "affected_questions_count": 0,
            "groups_count": 0,
            "warning": "Not implemented. Requires fuzzy matching or embeddings, deemed unsafe for C1.1."
        }
    }
