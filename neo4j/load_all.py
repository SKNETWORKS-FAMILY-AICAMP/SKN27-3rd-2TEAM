"""
Neo4j 전체 데이터 적재 스크립트 (Docker 자동 실행용).

실행 순서:
  1. MusicCatalog 노드 적재 (music_catalog.csv)
  2. 서브노드 적재 - Genre / Artist / Subgenre / Year
  3. Genre-Subgenre 엣지 연결용 CSV 생성 후 적재
  4. MusicCatalog 엣지 연결 - has_genre / has_subgenre / performed_by
  5. 분류 라벨 노드 및 엣지 적재 (music_catalog_scenarios.csv)

주의: music_catalog.csv 적재(1단계)가 선행되어야 나머지 단계가 작동한다.
"""
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# neo4j/ 폴더를 기준으로 common 모듈 탐색
sys.path.insert(0, str(Path(__file__).parent))

from common.connection import Neo4j_Connection
from common.querys import Query
from common.utils import (
    get_filepath,
    import_column,
    import_data,
    import_music_catalog_labels,
    remove_duplicate_genre_subgenre,
)


def wait_for_neo4j(retries: int = 20, interval: int = 5) -> Neo4j_Connection:
    for attempt in range(1, retries + 1):
        try:
            conn = Neo4j_Connection()
            conn.execute_query("RETURN 1")
            logger.info("Neo4j 연결 성공")
            return conn
        except Exception as exc:
            logger.warning("Neo4j 연결 대기 중 (%d/%d): %s", attempt, retries, exc)
            # 싱글톤 캐시 초기화 후 재시도
            Neo4j_Connection._instances.clear()
            time.sleep(interval)
    logger.error("Neo4j 연결 실패: 최대 재시도 횟수 초과")
    sys.exit(1)


def already_loaded(conn: Neo4j_Connection) -> bool:
    """5단계 적재가 모두 완료된 경우에만 True를 반환한다.
    마지막 단계(5)의 LabelEmotion 노드와 HAS_LABEL_EMOTION 엣지까지 확인한다."""
    checks = [
        ("MATCH (m:MusicCatalog) RETURN count(m) AS cnt", "MusicCatalog"),
        ("MATCH (g:Genre) RETURN count(g) AS cnt",        "Genre"),
        ("MATCH (a:Artist) RETURN count(a) AS cnt",       "Artist"),
        ("MATCH ()-[r:HAS_GENRE]->() RETURN count(r) AS cnt", "HAS_GENRE 엣지"),
        ("MATCH (l:LabelEmotion) RETURN count(l) AS cnt", "LabelEmotion"),
        ("MATCH ()-[r:HAS_LABEL_EMOTION]->() RETURN count(r) AS cnt", "HAS_LABEL_EMOTION 엣지"),
    ]
    for cypher, label in checks:
        result = conn.execute_query(cypher)
        cnt = result[0]["cnt"] if result else 0
        if cnt == 0:
            logger.info("미적재 감지 (%s = 0) → 전체 적재 시작", label)
            return False
        logger.info("적재 확인 (%s = %d)", label, cnt)
    logger.info("전체 적재 완료 상태 확인 → 적재 건너뜀")
    return True


def main():
    conn = wait_for_neo4j()

    if already_loaded(conn):
        return

    logger.info("=== Neo4j 전체 데이터 적재 시작 ===")

    # 1. MusicCatalog 노드
    logger.info("[1/5] MusicCatalog 노드 적재")
    import_data(path="music_catalog.csv", query_params=Query.music_catalog)

    # 2. 서브노드 (Genre / Artist / Subgenre / Year)
    logger.info("[2/5] 서브노드 적재")
    import_column(path="music_catalog.csv", column_name="playlist_genre",            query_params=Query.genres)
    import_column(path="music_catalog.csv", column_name="track_artist",               query_params=Query.artists)
    import_column(path="music_catalog.csv", column_name="playlist_subgenre",          query_params=Query.subgenres)
    import_column(path="music_catalog.csv", column_name="track_album_release_date",   query_params=Query.year)

    # 3. Genre-Subgenre 엣지 CSV 생성 → 적재
    logger.info("[3/5] Genre-Subgenre 엣지 적재")
    remove_duplicate_genre_subgenre(path=get_filepath("music_catalog.csv"))
    import_data(path="genre_subgenre.csv", query_params=Query.edge_has_genre_subgenre)

    # 4. MusicCatalog 엣지 연결
    logger.info("[4/5] MusicCatalog 엣지 연결")
    import_data(path="music_catalog.csv", query_params=Query.edge_has_genre)
    import_data(path="music_catalog.csv", query_params=Query.edge_has_subgenre)
    import_data(path="music_catalog.csv", query_params=Query.edge_performed_by)

    # 5. 분류 라벨 노드 및 엣지
    logger.info("[5/5] 분류 라벨 적재")
    import_music_catalog_labels()

    logger.info("=== Neo4j 전체 데이터 적재 완료 ===")


if __name__ == "__main__":
    main()
