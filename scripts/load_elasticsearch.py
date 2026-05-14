"""
Elasticsearch 데이터 적재 스크립트.

사용법:
  python scripts/load_elasticsearch.py                   # data/elasticsearch/ 폴더 전체
  python scripts/load_elasticsearch.py --file path.json  # 파일 지정
  python scripts/load_elasticsearch.py --recreate        # 인덱스 삭제 후 재생성

JSON 필수 필드:
  content_id         : 트랙 고유 ID (Neo4j track_id와 동일해야 함)
  content            : 검색 대상 텍스트
  metadata.track_id  : content_id와 동일 (ES 필터 키)

JSON 예시:
{
  "content_id": "트랙ID",
  "title": "곡 제목",
  "artist": "아티스트",
  "album": "앨범",
  "genre": ["pop"],
  "mood": ["calm"],
  "content": "ES 검색에 쓸 텍스트 설명",
  "metadata": {
    "track_id": "트랙ID",
    "artist": "아티스트",
    "genre": "pop"
  }
}
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from app.config import settings

DATA_DIR = ROOT / "data" / "elasticsearch"

INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "content_id": {"type": "keyword"},
            "title": {"type": "text"},
            "artist": {"type": "text"},
            "album": {"type": "text"},
            "genre": {"type": "keyword"},
            "mood": {"type": "keyword"},
            "content": {"type": "text"},
            "text": {"type": "text"},
            "metadata": {
                "type": "object",
                "properties": {
                    "track_id": {"type": "keyword"},
                    "song": {"type": "text"},
                    "track_name": {"type": "text"},
                    "artist": {"type": "text"},
                    "track_artist": {"type": "text"},
                    "genre": {"type": "text"},
                    "playlist_genre": {"type": "text"},
                    "emotion": {"type": "text"},
                    "text": {"type": "text"},
                },
            },
        }
    }
}


def build_client():
    try:
        from elasticsearch import Elasticsearch
    except ImportError:
        print("[ERROR] elasticsearch 패키지가 필요합니다: pip install elasticsearch")
        sys.exit(1)
    return Elasticsearch(settings.RIMAS_ELASTICSEARCH_URL, request_timeout=30)


def ensure_index(client, index: str, recreate: bool = False):
    if client.indices.exists(index=index):
        if recreate:
            client.indices.delete(index=index)
            print(f"[INFO] 인덱스 삭제: {index}")
        else:
            print(f"[INFO] 인덱스 이미 존재: {index}")
            return
    client.indices.create(index=index, body=INDEX_MAPPING)
    print(f"[INFO] 인덱스 생성: {index}")


def load_docs_from_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    # NDJSON (줄 단위 JSON)
    if text.startswith("{") and "\n" in text:
        docs = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                docs.append(json.loads(line))
        return docs
    parsed = json.loads(text)
    if isinstance(parsed, list):
        return parsed
    return [parsed]


def validate_doc(doc: dict, file_name: str, idx: int) -> bool:
    # content_id 없으면 doc_id로 자동 매핑
    if not doc.get("content_id"):
        if doc.get("doc_id"):
            doc["content_id"] = doc["doc_id"]
        else:
            print(f"[WARN] {file_name}[{idx}] content_id/doc_id 모두 누락 → 건너뜀")
            return False
    # metadata.track_id 없으면 content_id로 자동 채움
    doc.setdefault("metadata", {})
    if not doc["metadata"].get("track_id"):
        doc["metadata"]["track_id"] = doc["content_id"]
    return True


def bulk_index(client, index: str, docs: list[dict]) -> tuple[int, int]:
    from elasticsearch.helpers import bulk

    actions = [
        {"_index": index, "_id": doc["content_id"], "_source": doc}
        for doc in docs
    ]
    success, errors = bulk(client, actions, raise_on_error=False)
    return success, len(errors)


def already_loaded(client, index: str) -> bool:
    try:
        if not client.indices.exists(index=index):
            return False
        count = client.count(index=index)["count"]
        if count > 0:
            print(f"[INFO] 이미 적재된 데이터 감지 ({index}: {count}건) → 적재 건너뜀")
            return True
    except Exception:
        pass
    return False


def run(file_path: str | None, recreate: bool):
    client = build_client()
    index = settings.RIMAS_ELASTICSEARCH_INDEX

    try:
        client.info()
    except Exception as exc:
        print(f"[ERROR] Elasticsearch 연결 실패: {exc}")
        sys.exit(1)

    if not recreate and already_loaded(client, index):
        return

    ensure_index(client, index, recreate)

    if file_path:
        files = [Path(file_path)]
    else:
        files = sorted(DATA_DIR.glob("*.json"))
        if not files:
            print(f"[WARN] {DATA_DIR} 에 JSON 파일이 없습니다.")
            return

    total_ok = total_err = 0
    for f in files:
        print(f"[INFO] 처리 중: {f.name}")
        try:
            docs = load_docs_from_file(f)
        except json.JSONDecodeError as exc:
            print(f"[ERROR] JSON 파싱 실패 {f.name}: {exc}")
            continue

        valid_docs = [d for i, d in enumerate(docs) if validate_doc(d, f.name, i)]
        if not valid_docs:
            print(f"[WARN] {f.name}: 유효한 문서 없음")
            continue

        ok, err = bulk_index(client, index, valid_docs)
        total_ok += ok
        total_err += err
        print(f"[INFO] {f.name}: 성공 {ok}건, 실패 {err}건")

    print(f"\n[완료] 총 성공 {total_ok}건 / 실패 {total_err}건 (인덱스: {index})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Elasticsearch 데이터 적재")
    parser.add_argument("--file", help="특정 JSON 파일 경로")
    parser.add_argument("--recreate", action="store_true", help="인덱스 삭제 후 재생성")
    args = parser.parse_args()
    run(args.file, args.recreate)
