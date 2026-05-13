import csv
import json
import os
from collections import defaultdict


INCLUDE_SUMMARY_DOCS = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
INPUT_JSON_NAME = "spotify_20k_sample.json"
OUTPUT_CSV_PREFIX = "embedded_data_part"
SOURCE_NAME = "kaggle_spotify"
EMBEDDING_MODEL_NAME = "qwen3-embedding:0.6b"

start_index = 0
end_index = 20000
chunk_size = 1
batch_size = 32

fieldnames = [
    "doc_id",
    "doc_type",
    "content",
    "embedding",
    "source",
    "Artist(s)",
    "song",
    "text",
    "Length",
    "emotion",
    "Genre",
    "Album",
    "Release Date",
    "Key",
    "Tempo",
    "Loudness (db)",
    "Time signature",
    "Explicit",
    "Popularity",
    "Energy",
    "Danceability",
    "Positiveness",
    "Speechiness",
    "Liveness",
    "Acousticness",
    "Instrumentalness",
    "Good for Party",
    "Good for Work/Study",
    "Good for Relaxation/Meditation",
    "Good for Exercise",
    "Good for Running",
    "Good for Yoga/Stretching",
    "Good for Driving",
    "Good for Social Gatherings",
    "Good for Morning Routine",
    "Similar Songs"
]
FIELDNAMES = fieldnames


def safe_get(row: dict, key: str, default: str = "") -> str:
    value = row.get(key, default)
    if value is None:
        return default

    text = str(value).strip()
    if not text:
        return default

    return text


def build_track_content(row: dict) -> str:
    return (
        f"Song: {safe_get(row, 'song')}\n"
        f"Artist: {safe_get(row, 'Artist(s)')}\n"
        f"Album: {safe_get(row, 'Album')}\n"
        f"Genre: {safe_get(row, 'Genre')}\n"
        f"Emotion: {safe_get(row, 'emotion')}\n"
        f"Popularity: {safe_get(row, 'Popularity')}\n"
        "Audio features: "
        f"danceability {safe_get(row, 'Danceability')}, "
        f"energy {safe_get(row, 'Energy')}, "
        f"tempo {safe_get(row, 'Tempo')} BPM.\n"
        f"Lyrics: {safe_get(row, 'text')}\n"
        "This track may be useful for music recommendation, playlist search, "
        "mood-based retrieval, and genre-based discovery."
    )


def build_track_document(row: dict, row_index: int) -> dict:
    doc = {
        "doc_id": f"spotify_track_{row_index:06d}",
        "doc_type": "track",
        "content": build_track_content(row),
        "embedding": "",
        "source": SOURCE_NAME,
    }
    for k, v in row.items():
        if isinstance(v, (list, dict)):
            doc[k] = json.dumps(v, ensure_ascii=False)
        else:
            doc[k] = safe_get(row, k)
    return doc


def classify_mood(row: dict) -> str:
    energy = parse_float(safe_get(row, "energy"))
    valence = parse_float(safe_get(row, "valence"))
    danceability = parse_float(safe_get(row, "danceability"))

    if energy >= 0.75:
        return "high_energy"

    if valence >= 0.7:
        return "positive"

    if danceability >= 0.7:
        return "danceable"

    return "balanced"


def build_mood_content(mood: str) -> str:
    mood_label = mood.replace("_", " ")
    return (
        f"Mood: {mood_label}\n"
        "This summary document represents tracks grouped by mood for "
        "mood-based music retrieval and playlist recommendation."
    )


def write_documents_with_embeddings(
    documents: list[dict],
    embeddings,
    output_csv_path: str,
    fieldnames: list[str],
) -> int:
    if len(documents) != len(embeddings):
        raise ValueError("documents and embeddings must have the same length.")

    should_write_header = not os.path.exists(output_csv_path) or os.path.getsize(output_csv_path) == 0
    with open(output_csv_path, mode="a", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        if should_write_header:
            writer.writeheader()

        for document, vector in zip(documents, embeddings):
            row = {fieldname: document.get(fieldname, "") for fieldname in fieldnames}
            row["embedding"] = json.dumps(vector)
            writer.writerow(row)

    return len(documents)


def parse_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_doc_id_part(value: str) -> str:
    normalized = safe_get({"value": value}, "value", "unknown").lower()
    return "_".join(part for part in normalized.replace("&", "and").split() if part)


def read_spotify_rows(input_file_path: str) -> list[dict]:
    rows = []
    with open(input_file_path, mode="r", encoding="utf-8-sig", errors="ignore") as input_file:
        for line in input_file:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def build_genre_summary_content(genre: str, rows: list[dict]) -> str:
    subgenres = sorted({safe_get(row, "playlist_subgenre") for row in rows if safe_get(row, "playlist_subgenre")})
    track_count = len(rows)
    average_popularity = calculate_average(rows, "track_popularity")

    return (
        f"Genre: {genre}\n"
        f"Track count: {track_count}\n"
        f"Subgenres: {', '.join(subgenres)}\n"
        f"Average popularity: {average_popularity:.2f}\n"
        "This genre summary may be useful for genre-based music discovery and playlist search."
    )


def build_subgenre_summary_content(genre: str, subgenre: str, rows: list[dict]) -> str:
    track_count = len(rows)
    average_popularity = calculate_average(rows, "track_popularity")
    average_danceability = calculate_average(rows, "danceability")
    average_energy = calculate_average(rows, "energy")
    average_valence = calculate_average(rows, "valence")

    return (
        f"Genre: {genre}\n"
        f"Subgenre: {subgenre}\n"
        f"Track count: {track_count}\n"
        f"Average popularity: {average_popularity:.2f}\n"
        "Average audio features: "
        f"danceability {average_danceability:.3f}, "
        f"energy {average_energy:.3f}, "
        f"valence {average_valence:.3f}.\n"
        "This subgenre summary may be useful for subgenre-based retrieval and recommendation."
    )


def build_mood_summary_content(mood: str, rows: list[dict]) -> str:
    track_count = len(rows)
    average_energy = calculate_average(rows, "energy")
    average_valence = calculate_average(rows, "valence")
    average_danceability = calculate_average(rows, "danceability")

    return (
        f"{build_mood_content(mood)}\n"
        f"Track count: {track_count}\n"
        "Average audio features: "
        f"energy {average_energy:.3f}, "
        f"valence {average_valence:.3f}, "
        f"danceability {average_danceability:.3f}."
    )


def calculate_average(rows: list[dict], key: str) -> float:
    values = [parse_float(safe_get(row, key)) for row in rows if safe_get(row, key)]
    if not values:
        return 0.0

    return sum(values) / len(values)


def build_summary_document(
    doc_id: str,
    doc_type: str,
    content: str,
    genre: str = "",
    subgenre: str = "",
) -> dict:
    return {
        "doc_id": doc_id,
        "doc_type": doc_type,
        "content": content,
        "embedding": "",
        "track_id": "",
        "track_name": "",
        "artist": "",
        "album": "",
        "genre": genre,
        "subgenre": subgenre,
        "popularity": "",
        "danceability": "",
        "energy": "",
        "valence": "",
        "tempo": "",
        "duration_ms": "",
        "source": SOURCE_NAME,
    }


def build_genre_summary_documents(rows: list[dict]) -> list[dict]:
    rows_by_genre = defaultdict(list)
    for row in rows:
        genre = safe_get(row, "playlist_genre")
        if genre:
            rows_by_genre[genre].append(row)

    documents = []
    for genre in sorted(rows_by_genre):
        doc_id = f"spotify_genre_{normalize_doc_id_part(genre)}"
        documents.append(
            build_summary_document(
                doc_id=doc_id,
                doc_type="genre_summary",
                content=build_genre_summary_content(genre, rows_by_genre[genre]),
                genre=genre,
            )
        )

    return documents


def build_subgenre_summary_documents(rows: list[dict]) -> list[dict]:
    rows_by_subgenre = defaultdict(list)
    for row in rows:
        genre = safe_get(row, "playlist_genre")
        subgenre = safe_get(row, "playlist_subgenre")
        if genre and subgenre:
            rows_by_subgenre[(genre, subgenre)].append(row)

    documents = []
    for genre, subgenre in sorted(rows_by_subgenre):
        doc_id = f"spotify_subgenre_{normalize_doc_id_part(genre)}_{normalize_doc_id_part(subgenre)}"
        documents.append(
            build_summary_document(
                doc_id=doc_id,
                doc_type="subgenre_summary",
                content=build_subgenre_summary_content(genre, subgenre, rows_by_subgenre[(genre, subgenre)]),
                genre=genre,
                subgenre=subgenre,
            )
        )

    return documents


def build_mood_summary_documents(rows: list[dict]) -> list[dict]:
    rows_by_mood = defaultdict(list)
    for row in rows:
        rows_by_mood[classify_mood(row)].append(row)

    documents = []
    for mood in sorted(rows_by_mood):
        doc_id = f"spotify_mood_{normalize_doc_id_part(mood)}"
        documents.append(
            build_summary_document(
                doc_id=doc_id,
                doc_type="mood_summary",
                content=build_mood_summary_content(mood, rows_by_mood[mood]),
            )
        )

    return documents


def build_documents(rows: list[dict], include_summary_docs: bool) -> list[dict]:
    documents = [build_track_document(row, row_index) for row_index, row in enumerate(rows)]
    if not include_summary_docs:
        return documents

    documents.extend(build_genre_summary_documents(rows))
    documents.extend(build_subgenre_summary_documents(rows))
    documents.extend(build_mood_summary_documents(rows))
    return documents


def build_embedding_texts(documents: list[dict]) -> list[str]:
    texts = []
    for document in documents:
        content = safe_get(document, "content", " ")
        texts.append(content if content else " ")

    return texts


def output_csv_path_for_index(data_dir: str, document_index: int, chunk_size: int) -> str:
    current_part = document_index // chunk_size
    return os.path.join(data_dir, f"{OUTPUT_CSV_PREFIX}{current_part}.csv")


def group_batch_by_output_path(
    documents: list[dict],
    embeddings,
    batch_start_index: int,
    data_dir: str,
    chunk_size: int,
) -> list[tuple[str, list[dict], list]]:
    groups = []
    current_output_path = ""
    current_documents = []
    current_embeddings = []

    for offset, (document, embedding) in enumerate(zip(documents, embeddings)):
        document_index = batch_start_index + offset
        output_csv_path = output_csv_path_for_index(data_dir, document_index, chunk_size)

        if current_output_path and output_csv_path != current_output_path:
            groups.append((current_output_path, current_documents, current_embeddings))
            current_documents = []
            current_embeddings = []

        current_output_path = output_csv_path
        current_documents.append(document)
        current_embeddings.append(embedding)

    if current_documents:
        groups.append((current_output_path, current_documents, current_embeddings))

    return groups


def main() -> None:
    from langchain_ollama import OllamaEmbeddings
    from tqdm import tqdm

    input_file_path = os.path.join(DATA_DIR, INPUT_JSON_NAME)
    if not os.path.exists(input_file_path):
        raise FileNotFoundError(f"처리할 JSON 파일이 없습니다: {input_file_path}")

    print(f"처리할 파일: {input_file_path}")
    rows = read_spotify_rows(input_file_path)
    print(f"로드된 전체 row 수: {len(rows)}")

    documents = build_documents(rows, INCLUDE_SUMMARY_DOCS)
    print(f"생성된 전체 문서 수: {len(documents)}")
    print(f"임베딩 결과를 {chunk_size}개 단위로 분할하여 embedded_data_part{{n}}.csv에 저장합니다.")

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)
    embedded_count = 0

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    actual_end = min(end_index + 1, len(documents))

    for index in tqdm(
        range(start_index, actual_end, batch_size),
        desc="임베딩 진행률",
        initial=start_index,
        total=actual_end,
    ):
        current_batch_end = min(index + batch_size, actual_end)
        batch_documents = documents[index : current_batch_end]
        texts_to_embed = build_embedding_texts(batch_documents)

        try:
            batch_embeddings = embeddings.embed_documents(texts_to_embed)
        except Exception as exc:
            print(f"\n임베딩 처리 중 오류 발생 (문서 인덱스 {index}): {exc}")
            continue

        for current_output_csv, group_documents, group_embeddings in group_batch_by_output_path(
            documents=batch_documents,
            embeddings=batch_embeddings,
            batch_start_index=index,
            data_dir=OUTPUT_DIR,
            chunk_size=chunk_size,
        ):
            embedded_count += write_documents_with_embeddings(
                group_documents,
                group_embeddings,
                current_output_csv,
                fieldnames,
            )

    print(f"생성된 임베딩 문서 수: {embedded_count}")
    print("전체 CSV 파일 저장 완료.")


if __name__ == "__main__":
    main()


# Elasticsearch 인덱스 생성 예시는 CSV 생성 목적과 분리되어 현재 실행하지 않습니다.
# 필요 시 CSV 생성 완료 후 별도 인덱싱 스크립트에서 es_client를 import하여 사용하세요.
#
# index_name = "rag_keywords"
#
# if es_client.indices.exists(index=index_name):
#     es_client.indices.delete(index=index_name)
#     print(f"기존 인덱스 '{index_name}' 삭제")
#
# index_mapping = {
#     "mappings": {
#         "properties": {
#             "content": {
#                 "type": "text",
#                 "analyzer": "standard",
#             },
#             "embedding": {
#                 "type": "dense_vector",
#                 "dims": 1024,
#                 "index": True,
#                 "similarity": "cosine",
#             },
#             "metadata": {
#                 "type": "object",
#                 "enabled": True,
#             },
#         }
#     }
# }
#
# es_client.indices.create(index=index_name, body=index_mapping)
# print(f"인덱스 '{index_name}' 생성 완료")
