import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NEO4J_CATALOG = ROOT / "neo4j" / "data" / "music_catalog.csv"
DEFAULT_ES_DIR = ROOT / "data" / "elasticsearch"


def normalize_track_key(
    *,
    title: object,
    artist: object,
    album: object,
    duration_ms: object,
) -> tuple[str, str, str, int | None]:
    return (
        _normalize_text(title),
        _normalize_text(artist),
        _normalize_text(album),
        _normalize_duration_ms(duration_ms),
    )


def load_neo4j_catalog(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        return list(csv.DictReader(fp))


def load_es_documents(paths: Iterable[Path]) -> list[dict]:
    documents = []
    for path in paths:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue

        parsed_docs = _parse_json_or_ndjson(text)
        for doc in parsed_docs:
            content_id = str(doc.get("content_id") or doc.get("doc_id") or "").strip()
            if not content_id:
                continue
            normalized = dict(doc)
            normalized["content_id"] = content_id
            documents.append(normalized)
    return documents


def discover_es_files(es_dir: Path) -> list[Path]:
    return sorted(es_dir.glob("*.json"))


def build_alignment_report(
    neo4j_rows: list[dict],
    es_docs: list[dict],
    sample_limit: int = 20,
) -> dict:
    es_by_key = _index_es_docs(es_docs)
    exact_matches = []
    duplicate_matches = []
    unmatched_neo4j = []

    for row in neo4j_rows:
        track_id = str(row.get("track_id") or "").strip()
        if not track_id:
            continue

        key = _neo4j_key(row)
        matched_docs = es_by_key.get(key, [])
        if len(matched_docs) == 1:
            exact_matches.append(_build_exact_match(row, matched_docs[0]))
            continue
        if len(matched_docs) > 1:
            duplicate_matches.append(_build_duplicate_match(row, matched_docs))
            continue
        unmatched_neo4j.append(_build_unmatched(row))

    return {
        "summary": {
            "neo4j_rows": len(neo4j_rows),
            "es_documents": len(es_docs),
            "exact_matches": len(exact_matches),
            "duplicate_matches": len(duplicate_matches),
            "unmatched_neo4j": len(unmatched_neo4j),
        },
        "exact_matches": exact_matches[:sample_limit],
        "duplicate_matches": duplicate_matches[:sample_limit],
        "unmatched_neo4j": unmatched_neo4j[:sample_limit],
    }


def build_aligned_es_documents(neo4j_rows: list[dict], es_docs: list[dict]) -> list[dict]:
    es_by_key = _index_es_docs(es_docs)
    aligned_docs = []

    for row in neo4j_rows:
        track_id = str(row.get("track_id") or "").strip()
        if not track_id:
            continue

        matched_docs = es_by_key.get(_neo4j_key(row), [])
        if len(matched_docs) != 1:
            continue

        source_doc = matched_docs[0]
        legacy_content_id = str(source_doc.get("content_id") or "")
        aligned_doc = dict(source_doc)
        aligned_doc["content_id"] = track_id
        aligned_doc.setdefault("metadata", {})
        aligned_doc["metadata"] = dict(aligned_doc["metadata"])
        aligned_doc["metadata"]["track_id"] = track_id
        if legacy_content_id and legacy_content_id != track_id:
            aligned_doc["metadata"]["legacy_content_id"] = legacy_content_id
        aligned_docs.append(aligned_doc)

    return aligned_docs


def write_report(report: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_ndjson(documents: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as fp:
        for doc in documents:
            fp.write(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
            fp.write("\n")


def _index_es_docs(es_docs: list[dict]) -> dict[tuple[str, str, str, int | None], list[dict]]:
    indexed = defaultdict(list)
    for doc in es_docs:
        key = _es_key(doc)
        if not key[0] or not key[1]:
            continue
        indexed[key].append(doc)
    return indexed


def _neo4j_key(row: dict) -> tuple[str, str, str, int | None]:
    return normalize_track_key(
        title=row.get("track_name"),
        artist=row.get("track_artist"),
        album=row.get("track_album_name"),
        duration_ms=row.get("duration_ms"),
    )


def _es_key(doc: dict) -> tuple[str, str, str, int | None]:
    metadata = doc.get("metadata") or {}
    return normalize_track_key(
        title=_first_value(doc.get("song"), doc.get("title"), doc.get("track_name"), metadata.get("song")),
        artist=_first_value(
            doc.get("artist"),
            doc.get("track_artist"),
            metadata.get("artist"),
            metadata.get("track_artist"),
        ),
        album=_first_value(doc.get("album"), doc.get("track_album_name"), metadata.get("album")),
        duration_ms=_first_value(doc.get("duration_ms"), doc.get("length"), metadata.get("duration_ms")),
    )


def _build_exact_match(row: dict, doc: dict) -> dict:
    return {
        "neo4j_track_id": str(row.get("track_id") or ""),
        "es_content_id": str(doc.get("content_id") or ""),
        "track_name": str(row.get("track_name") or ""),
        "track_artist": str(row.get("track_artist") or ""),
    }


def _build_duplicate_match(row: dict, docs: list[dict]) -> dict:
    return {
        "neo4j_track_id": str(row.get("track_id") or ""),
        "track_name": str(row.get("track_name") or ""),
        "track_artist": str(row.get("track_artist") or ""),
        "es_content_ids": [str(doc.get("content_id") or "") for doc in docs],
    }


def _build_unmatched(row: dict) -> dict:
    return {
        "neo4j_track_id": str(row.get("track_id") or ""),
        "track_name": str(row.get("track_name") or ""),
        "track_artist": str(row.get("track_artist") or ""),
        "track_album_name": str(row.get("track_album_name") or ""),
        "duration_ms": str(row.get("duration_ms") or ""),
    }


def _parse_json_or_ndjson(text: str) -> list[dict]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        return [parsed]

    docs = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            docs.append(parsed)
    return docs


def _normalize_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _normalize_duration_ms(value: object) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if ":" in text:
        parts = text.split(":")
        try:
            seconds = int(parts[-1])
            minutes = int(parts[-2])
            hours = int(parts[-3]) if len(parts) == 3 else 0
        except ValueError:
            return None
        return ((hours * 60 + minutes) * 60 + seconds) * 1000
    try:
        return int(float(text))
    except ValueError:
        return None


def _first_value(*values: object) -> object:
    for value in values:
        if value is None:
            continue
        if str(value).strip():
            return value
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Neo4j track_id and Elasticsearch content_id alignment.")
    parser.add_argument("--neo4j-catalog", type=Path, default=DEFAULT_NEO4J_CATALOG)
    parser.add_argument("--es-dir", type=Path, default=DEFAULT_ES_DIR)
    parser.add_argument("--output", type=Path, default=ROOT / "tmp" / "es_neo4j_id_alignment_report.json")
    parser.add_argument("--aligned-output", type=Path)
    parser.add_argument("--sample-limit", type=int, default=20)
    args = parser.parse_args()

    neo4j_rows = load_neo4j_catalog(args.neo4j_catalog)
    es_docs = load_es_documents(discover_es_files(args.es_dir))
    report = build_alignment_report(neo4j_rows, es_docs, sample_limit=args.sample_limit)
    write_report(report, args.output)

    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"[INFO] report written: {args.output}")

    if args.aligned_output:
        aligned_docs = build_aligned_es_documents(neo4j_rows, es_docs)
        write_ndjson(aligned_docs, args.aligned_output)
        print(f"[INFO] aligned documents written: {args.aligned_output} ({len(aligned_docs)} docs)")


if __name__ == "__main__":
    main()
