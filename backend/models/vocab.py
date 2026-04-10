import json
from db import get_connection
from typing import List, Dict

def replace_project_vocab(project_id, vocab_list):
    """
    用传入的 vocab_list 覆盖某个 project 的所有词汇：
    1）先删掉该 project_id 下面的所有 vocab
    2）再把 vocab_list 逐条插入
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM vocab WHERE project_id=%s", (project_id,))

            sql = """
                INSERT INTO vocab (
                    project_id,
                    vocab_entry_id,
                    category,
                    word,
                    level,
                    full_match,
                    partial_match,
                    relaxed_match,
                    explainable,
                    cognate,
                    origin_type,
                    borrow_source,
                    borrow_source_other,
                    borrow_change,
                    borrow_change_other,
                    time_event_type,
                    time_lower,
                    time_lower_era,
                    time_upper,
                    time_upper_era,
                    evidence,
                    recorded_at,
                    word_data_json,
                    comp_data_json
                ) VALUES (
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,
                    %s,%s,
                    %s,%s,%s,
                    %s,%s,
                    %s,%s,%s,
                    %s,%s,
                    %s,%s,
                    %s,%s
                )
            """

            for v in (vocab_list or []):
                if not isinstance(v, dict):
                    continue

                time_info = v.get("timeInfo") or {}

                explainable_val = v.get("explainable")
                if explainable_val is None:
                    explainable_db = None
                else:
                    explainable_db = 1 if explainable_val else 0

                cognate_val = v.get("cognate")
                if cognate_val is None:
                    cognate_db = None
                else:
                    cognate_db = 1 if cognate_val else 0

                cursor.execute(sql, (
                    project_id,
                    v.get("id"),
                    v.get("category"),
                    v.get("word"),
                    v.get("level"),

                    1 if v.get("fullMatch") else 0,
                    1 if v.get("partialMatch") else 0,
                    1 if v.get("relaxedMatch") else 0,

                    explainable_db,
                    cognate_db,

                    v.get("originType"),
                    v.get("borrowSource"),
                    v.get("borrowSourceOther"),
                    v.get("borrowChange"),
                    v.get("borrowChangeOther"),

                    time_info.get("eventType"),
                    time_info.get("lower"),
                    time_info.get("lowerEra"),
                    time_info.get("upper"),
                    time_info.get("upperEra"),

                    v.get("evidence"),
                    v.get("recordedAt"),

                    json.dumps(v.get("wordData"), ensure_ascii=False) if v.get("wordData") is not None else None,
                    json.dumps(v.get("compData"), ensure_ascii=False) if v.get("compData") is not None else None,
                ))

        conn.commit()
    finally:
        conn.close()

def get_project_vocab(project_id: str) -> List[Dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM vocab WHERE project_id=%s ORDER BY id ASC",
                (project_id,)
            )
            return cursor.fetchall()
    finally:
        conn.close()
