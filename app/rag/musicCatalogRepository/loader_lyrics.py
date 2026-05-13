import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
INPUT_JSON_NAME = "spotify_60k_sampled.json"
OUTPUT_JSON_PREFIX = "embedded_data_part"
SOURCE_NAME = "kaggle_spotify"
EMBEDDING_MODEL_NAME = "qwen3-embedding:0.6b"

start_index = 55505
end_index = None
chunk_size = 500
batch_size = 32

FIELDNAMES = [
    "doc_id",
    "doc_type",
    "content",
    "embedding",
    # --- 메타데이터 (임베딩 안됨) ---
    "artist",
    "song",
    "length",
    "emotion",
    "genre",
    "album",
    "release_date",
    "key",
    "tempo",
    "loudness_db",
    "time_signature",
    "explicit",
    "popularity",
    "energy",
    "danceability",
    "positiveness",
    "speechiness",
    "liveness",
    "acousticness",
    "instrumentalness",
    "good_for_party",
    "good_for_work_study",
    "good_for_relaxation",
    "good_for_exercise",
    "good_for_running",
    "good_for_yoga",
    "good_for_driving",
    "good_for_social",
    "good_for_morning",
    "similar_songs",
    "source",
]


def safe_str(value, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip() or default


def read_lyrics_rows(input_json_path: str) -> list[dict]:
    rows = []
    with open(input_json_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_lyrics_document(row: dict, row_index: int) -> dict:
    """가사(text)를 content로, 나머지 모든 필드를 메타데이터로."""
    return {
        "doc_id": f"lyrics_{row_index:06d}",
        "doc_type": "lyrics",
        "content": safe_str(row.get("text")),
        "embedding": "",
        "artist": safe_str(row.get("Artist(s)")),
        "song": safe_str(row.get("song")),
        "length": safe_str(row.get("Length")),
        "emotion": safe_str(row.get("emotion")),
        "genre": safe_str(row.get("Genre")),
        "album": safe_str(row.get("Album")),
        "release_date": safe_str(row.get("Release Date")),
        "key": safe_str(row.get("Key")),
        "tempo": safe_str(row.get("Tempo")),
        "loudness_db": safe_str(row.get("Loudness (db)")),
        "time_signature": safe_str(row.get("Time signature")),
        "explicit": safe_str(row.get("Explicit")),
        "popularity": safe_str(row.get("Popularity")),
        "energy": safe_str(row.get("Energy")),
        "danceability": safe_str(row.get("Danceability")),
        "positiveness": safe_str(row.get("Positiveness")),
        "speechiness": safe_str(row.get("Speechiness")),
        "liveness": safe_str(row.get("Liveness")),
        "acousticness": safe_str(row.get("Acousticness")),
        "instrumentalness": safe_str(row.get("Instrumentalness")),
        "good_for_party": safe_str(row.get("Good for Party")),
        "good_for_work_study": safe_str(row.get("Good for Work/Study")),
        "good_for_relaxation": safe_str(row.get("Good for Relaxation/Meditation")),
        "good_for_exercise": safe_str(row.get("Good for Exercise")),
        "good_for_running": safe_str(row.get("Good for Running")),
        "good_for_yoga": safe_str(row.get("Good for Yoga/Stretching")),
        "good_for_driving": safe_str(row.get("Good for Driving")),
        "good_for_social": safe_str(row.get("Good for Social Gatherings")),
        "good_for_morning": safe_str(row.get("Good for Morning Routine")),
        "similar_songs": json.dumps(row.get("Similar Songs", []), ensure_ascii=False),
        "source": SOURCE_NAME,
    }


def build_documents(rows: list[dict]) -> list[dict]:
    return [build_lyrics_document(row, i) for i, row in enumerate(rows)]


def write_documents_with_embeddings(
    documents: list[dict],
    embeddings: list,
    output_json_path: str,
) -> int:
    if len(documents) != len(embeddings):
        raise ValueError("documents와 embeddings 길이가 다릅니다.")

    with open(output_json_path, mode="a", encoding="utf-8") as f:
        for doc, vector in zip(documents, embeddings):
            record = {k: doc.get(k, "") for k in FIELDNAMES}
            record["embedding"] = vector
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return len(documents)


def output_json_path_for_index(document_index: int) -> str:
    part = document_index // chunk_size
    return os.path.join(OUTPUT_DIR, f"{OUTPUT_JSON_PREFIX}{part}.json")


def group_batch_by_output_path(
    documents: list[dict],
    embeddings: list,
    batch_start_index: int,
) -> list[tuple[str, list[dict], list]]:
    groups: list[tuple[str, list[dict], list]] = []
    current_path = ""
    current_docs: list[dict] = []
    current_embs: list = []

    for offset, (doc, emb) in enumerate(zip(documents, embeddings)):
        path = output_json_path_for_index(batch_start_index + offset)
        if current_path and path != current_path:
            groups.append((current_path, current_docs, current_embs))
            current_docs, current_embs = [], []
        current_path = path
        current_docs.append(doc)
        current_embs.append(emb)

    if current_docs:
        groups.append((current_path, current_docs, current_embs))

    return groups


def main() -> None:
    from langchain_ollama import OllamaEmbeddings
    from tqdm import tqdm

    input_json_path = os.path.join(DATA_DIR, INPUT_JSON_NAME)
    if not os.path.exists(input_json_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {input_json_path}")

    print(f"처리할 파일: {input_json_path}")
    rows = read_lyrics_rows(input_json_path)
    print(f"로드된 행 수: {len(rows)}")

    documents = build_documents(rows)
    print(f"생성된 문서 수: {len(documents)}")

    actual_end = end_index if end_index is not None else len(documents)
    actual_end = min(actual_end, len(documents))
    target_count = actual_end - start_index
    print(f"처리 범위: [{start_index}, {actual_end}) — 총 {target_count}개")
    print(f"임베딩 결과를 {chunk_size}개 단위로 {OUTPUT_JSON_PREFIX}{{n}}.json에 저장합니다.")

    embedder = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)
    embedded_count = 0

    for index in tqdm(
        range(start_index, actual_end, batch_size),
        desc="임베딩 진행률",
        total=(target_count + batch_size - 1) // batch_size,
    ):
        batch_docs = documents[index : index + batch_size]
        texts = [doc["content"] if doc["content"] else " " for doc in batch_docs]

        try:
            batch_embeddings = embedder.embed_documents(texts)
        except Exception as exc:
            print(f"\n임베딩 오류 (인덱스 {index}): {exc}")
            continue

        for json_path, group_docs, group_embs in group_batch_by_output_path(
            batch_docs, batch_embeddings, index
        ):
            embedded_count += write_documents_with_embeddings(
                group_docs, group_embs, json_path
            )

    print(f"\n임베딩 완료: {embedded_count}개 문서")
    print("CSV 파일 저장 완료.")


if __name__ == "__main__":
    main()
