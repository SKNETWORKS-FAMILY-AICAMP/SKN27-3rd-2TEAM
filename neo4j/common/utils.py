# 로그
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 패키지
import pandas as pd
from pathlib import Path
from common.connection import Neo4j_Connection
from common.constant import (
    MUSIC_CATALOG_SCENARIOS_CSV_FILENAME,
    LABEL_CATEGORY_COLUMNS,
    LABEL_CSV_KEY_COLUMN,
    LABEL_CSV_TAG_SEPARATOR,
)
from typing import Optional


####################################################################
# 파일 경로 반환 함수 
####################################################################
def get_filepath(file_name:str) -> str:
    """ 파일 이름을 넣었을 때 data 폴더 경로의 이름을 반환하는 함수 """
    _DATA_DIR = Path(__file__).resolve().parent.parent / "data"
    return _DATA_DIR / file_name



####################################################################
# 쿼리 실행 함수 
####################################################################
def execute_query(values: list, query_params=None, batch_size: int = 1000):
    """
    UNWIND 쿼리용 실행 함수.
    values 전체를 rows 파라미터로 넘겨 batch 단위 실행.
    """

    driver = Neo4j_Connection()
    total_count = len(values)

    for start in range(0, total_count, batch_size):
        batch = values[start:start + batch_size]
        query, parameters = query_params(batch)
        driver.execute_query(query=query,parameters=parameters)

        logger.info(f"{start + len(batch)} / {total_count}개 적재 진행")

    logger.info(f"데이터 {total_count}개 적재 완료!")

##--------------------------------------------------------------------------------------------------##
def import_data(path: str = None, query_params=None, batch_size: int = 1000):
    """
    CSV 데이터를 batch 단위로 읽어
    query_params(rows)로 얻은 UNWIND Cypher·파라미터를 실행해 그래프 DB에 적재한다.
    """

    df = pd.read_csv(get_filepath(path))
    driver = Neo4j_Connection()

    records = df.to_dict("records")
    total_count = len(records)

    for start in range(0, total_count, batch_size):
        batch = records[start:start + batch_size]

        query, parameters = query_params(batch)

        driver.execute_query(
            query=query,
            parameters=parameters
        )

        logger.info(f"{start + len(batch)} / {total_count}개 적재 완료")

    logger.info(f"데이터 {total_count}개 적재 완료!")

##--------------------------------------------------------------------------------------------------##
def import_column(path: str = None,column_name: str = None,query_params=None,batch_size: int = 1000):
    """
    특정 컬럼의 unique 값들을 batch 단위로 적재한다.

    query_params(values)는
    UNWIND 기반 쿼리와 parameters를 반환해야 한다.
    """

    df = pd.read_csv(get_filepath(path))
    values = (df[column_name].dropna().unique().tolist())
    total_count = len(values)

    if total_count == 0:
        logger.warning(f"컬럼 {column_name!r} 에 적재할 데이터가 없습니다.")
        return

    driver = Neo4j_Connection()

    for start in range(0, total_count, batch_size):
        batch = values[start:start + batch_size]
        query, parameters = query_params(batch)
        driver.execute_query(query=query,parameters=parameters)
        logger.info(f"{column_name!r} "f"{start + len(batch)} / {total_count}개 적재 완료")

    logger.info(f"컬럼 {column_name!r} "f"유니크 {total_count}개 적재 완료")


def split_label_csv_cell(value, sep: str) -> list[str]:
    """라벨 CSV 셀의 세미콜론 구분 토큰 목록을 리스트로 정규화한다."""
    if value is None or pd.isna(value):
        return []
    s = str(value).strip()
    if not s:
        return []
    return [p.strip() for p in str(s).split(sep) if p.strip()]


def import_music_catalog_labels(batch_size: int = 1000) -> None:
    """
    music_catalog_scenarios.csv의 각 카테고리 라벨 열(LABEL_CATEGORY_COLUMNS)마다
    해당 Neo4j 값 노드(Label*)를 MERGE하고 MusicCatalog(track_id)와 HAS_LABEL_* 로 연결한다.
    선행으로 music_catalog 적재가 있어야 track_id 매칭된다.
    """
    from common.querys import Query

    df = pd.read_csv(get_filepath(MUSIC_CATALOG_SCENARIOS_CSV_FILENAME))
    df = df[:5] # 테스트 용으로 5열 까지만 
    tag_pairs: set[tuple[str, str]] = set()
    link_rows: list[dict] = []

    for rec in df.to_dict("records"):
        tid_raw = rec.get(LABEL_CSV_KEY_COLUMN)
        if tid_raw is None or (isinstance(tid_raw, float) and pd.isna(tid_raw)):
            continue
        track_id = str(tid_raw).strip()
        if not track_id:
            continue
        for col in LABEL_CATEGORY_COLUMNS:
            if col not in rec:
                continue
            for tag in split_label_csv_cell(rec.get(col), LABEL_CSV_TAG_SEPARATOR):
                tag_pairs.add((col, tag))
                link_rows.append({"track_id": track_id, "column": col, "tag_id": tag})

    driver = Neo4j_Connection()

    for column in LABEL_CATEGORY_COLUMNS:
        col_tags = sorted({t for c, t in tag_pairs if c == column})
        tag_param_rows = [{"tag_id": t} for t in col_tags]
        total_tags = len(tag_param_rows)
        for start in range(0, total_tags, batch_size):
            batch = tag_param_rows[start : start + batch_size]
            query, parameters = Query.label_category_values_merge(column, batch)
            driver.execute_query(query=query, parameters=parameters)
            logger.info(
                "카테고리 라벨 열 %r 값 노드 %s / %s 적재",
                column,
                start + len(batch),
                total_tags,
            )

        col_links = [
            {"track_id": r["track_id"], "tag_id": r["tag_id"]}
            for r in link_rows
            if r["column"] == column
        ]
        total_links = len(col_links)
        for start in range(0, total_links, batch_size):
            batch = col_links[start : start + batch_size]
            query, parameters = Query.label_category_link(column, batch)
            driver.execute_query(query=query, parameters=parameters)
            logger.info(
                "카테고리 라벨 열 %r 관계 %s / %s 적재",
                column,
                start + len(batch),
                total_links,
            )

    logger.info("music_catalog_scenarios 라벨 열 적재 완료")


############################################################
# 쿼리 문자열 정규화 함수 
############################################################
def split_multi(value) -> list[str]:
    """CSV 쉼표 구분 필드를 리스트로 정규화. 비어 있으면 빈 리스트."""
    if value is None or pd.isna(value):
        return []
    s = str(value).strip()
    if not s:
        return []
    return [p.strip() for p in s.split(",") if p.strip()]


def scalar_or_none(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return value


###########################################################
# 날짜 가공 유틸 함수
###########################################################
def extract_release_year(release_date: str | None) -> Optional[int]:
    """
    Spotify track_album_release_date 값에서 발매 연도만 추출한다.

    [input]
    "2019-04-12"
    "2020"
    "2018-01"
    None
    ""

    [output]
    2019
    2020
    2018
    None
    """

    if release_date is None:
        return None

    release_date_text = str(release_date).strip()

    if not release_date_text:
        return None

    year_text = release_date_text[:4]

    if not year_text.isdigit():
        return None

    return int(year_text)


###########################################################
# 장르 / 서브장르 조합 중복제거 -> csv 파일로 neo4j/data 폴더에 저장 
###########################################################
def remove_duplicate_genre_subgenre(path: str):
    """
    df 에서 장르 / 서브장르 조합 중복제거 
    같은 row의 playlist_genres와 playlist_subgenre를 하나의 튜플로 묶은다음 set에 넣어서 중복을 제거하고 나서 
    다시 해당 데이터를 별도의 dataframe으로 반환 한다. 
    반환 시에는 하나의 튜플이었던 데이터를 다시 genres, subgenres로 분리해야 한다. 
    """
    # 파일 path 에서 데이터를 읽어온다. 
    df = pd.read_csv(path)

    # df에서 playlist_genres와 playlist_subgenre를 하나의 튜플로 묶은다음 set에 넣어서 중복을 제거한다.
    genre_subgenre_set = set(zip(df["playlist_genre"], df["playlist_subgenre"]))

    # 중복을 제거한 튜플을 가지고 다시 dataframe으로 변환한다. 
    # 변환 시에는 튜플에서 [0] 인덱스는 장르, [1] 인덱스는 서브장르여야 한다. 
    genre_subgenre_df = pd.DataFrame(genre_subgenre_set, columns=["genres", "subgenres"])

    # csv 파일로 neo4j/data 폴더에 저장 
    genre_subgenre_df.to_csv(get_filepath("genre_subgenre.csv"), index=False)
