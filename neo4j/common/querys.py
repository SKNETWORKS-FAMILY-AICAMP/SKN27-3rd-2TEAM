# 로그
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 패키지
import pandas as pd

# 모듈
from common.utils import extract_release_year, split_multi, scalar_or_none
from common.constant import (
    KagMoodLabel,
    KagTempoLabel,
    KagNodeLabel,
    KagRelationType,
    SCENARIO_DIM_TO_LABEL_AND_REL,
)


####################################################################
# 실행할 쿼리 목록 정의
####################################################################

from common.utils import extract_release_year, scalar_or_none


class Query:
    """music_catalog.csv 적재에 필요한 Cypher query와 파라미터를 만든다."""

    @staticmethod
    def music_catalog(rows: list[dict]) -> tuple[str, dict]:
        query = """
        UNWIND $rows AS row

        MERGE (mc:MusicCatalog {track_id: row.track_id})
        SET mc.name = row.track_name,
            mc.track_name = row.track_name,
            mc.track_artist = row.track_artist,
            mc.track_popularity = row.track_popularity,
            mc.track_album_id = row.track_album_id,
            mc.track_album_name = row.track_album_name,
            mc.track_album_release_date = row.track_album_release_date,
            mc.playlist_name = row.playlist_name,
            mc.playlist_id = row.playlist_id,
            mc.playlist_genre = row.playlist_genre,
            mc.playlist_subgenre = row.playlist_subgenre,
            mc.danceability = row.danceability,
            mc.energy = row.energy,
            mc.`key` = row.key,
            mc.loudness = row.loudness,
            mc.mode = row.mode,
            mc.speechiness = row.speechiness,
            mc.acousticness = row.acousticness,
            mc.instrumentalness = row.instrumentalness,
            mc.liveness = row.liveness,
            mc.valence = row.valence,
            mc.tempo = row.tempo,
            mc.duration_ms = row.duration_ms
        """

        parameters = {
            "rows": [
                {
                    "track_id": str(row["track_id"]).strip(),
                    "track_name": scalar_or_none(row.get("track_name")),
                    "track_artist": scalar_or_none(row.get("track_artist")),
                    "track_popularity": scalar_or_none(row.get("track_popularity")),
                    "track_album_id": scalar_or_none(row.get("track_album_id")),
                    "track_album_name": scalar_or_none(row.get("track_album_name")),
                    "track_album_release_date": scalar_or_none(row.get("track_album_release_date")),
                    "playlist_name": scalar_or_none(row.get("playlist_name")),
                    "playlist_id": scalar_or_none(row.get("playlist_id")),
                    "playlist_genre": scalar_or_none(row.get("playlist_genre")),
                    "playlist_subgenre": scalar_or_none(row.get("playlist_subgenre")),
                    "danceability": scalar_or_none(row.get("danceability")),
                    "energy": scalar_or_none(row.get("energy")),
                    "key": scalar_or_none(row.get("key")),
                    "loudness": scalar_or_none(row.get("loudness")),
                    "mode": scalar_or_none(row.get("mode")),
                    "speechiness": scalar_or_none(row.get("speechiness")),
                    "acousticness": scalar_or_none(row.get("acousticness")),
                    "instrumentalness": scalar_or_none(row.get("instrumentalness")),
                    "liveness": scalar_or_none(row.get("liveness")),
                    "valence": scalar_or_none(row.get("valence")),
                    "tempo": scalar_or_none(row.get("tempo")),
                    "duration_ms": scalar_or_none(row.get("duration_ms")),
                }
                for row in rows
                if scalar_or_none(row.get("track_id")) is not None
            ]
        }

        return query, parameters

    @staticmethod
    def genres(values: list[str]) -> tuple[str, dict]:
        query = """
        UNWIND $values AS value
        MERGE (:Genre {genre: value})
        """
        return query, {"values": Query._clean_unique(values)}

    @staticmethod
    def artists(values: list[str]) -> tuple[str, dict]:
        query = """
        UNWIND $values AS value
        MERGE (:Artist {artist: value})
        """
        return query, {"values": Query._clean_unique(values)}

    @staticmethod
    def subgenres(values: list[str]) -> tuple[str, dict]:
        query = """
        UNWIND $values AS value
        MERGE (:SubGenre {subgenre: value})
        """
        return query, {"values": Query._clean_unique(values)}

    @staticmethod
    def year(values: list[str | None]) -> tuple[str, dict]:
        query = """
        UNWIND $years AS year
        MERGE (:ReleaseYear {year: year})
        """
        years = {
            year
            for value in values
            if (year := extract_release_year(value)) is not None
        }
        return query, {"years": sorted(years)}

    @staticmethod
    def edge_has_genre(rows: list[dict]) -> tuple[str, dict]:
        query = """
        UNWIND $rows AS row

        MATCH (mc:MusicCatalog {track_id: row.track_id})
        MATCH (g:Genre {genre: row.genre})
        MERGE (mc)-[:HAS_GENRE]->(g)
        """
        return query, {"rows": Query._track_value_rows(rows, "playlist_genre", "genre")}

    @staticmethod
    def edge_has_subgenre(rows: list[dict]) -> tuple[str, dict]:
        query = """
        UNWIND $rows AS row

        MATCH (mc:MusicCatalog {track_id: row.track_id})
        MATCH (sg:SubGenre {subgenre: row.subgenre})
        MERGE (mc)-[:HAS_SUBGENRE]->(sg)
        """
        return query, {"rows": Query._track_value_rows(rows, "playlist_subgenre", "subgenre")}

    @staticmethod
    def edge_performed_by(rows: list[dict]) -> tuple[str, dict]:
        query = """
        UNWIND $rows AS row

        MATCH (mc:MusicCatalog {track_id: row.track_id})
        MATCH (a:Artist {artist: row.artist})
        MERGE (mc)-[:PERFORMED_BY]->(a)
        """
        return query, {"rows": Query._track_value_rows(rows, "track_artist", "artist")}

    @staticmethod
    def edge_released_in(rows: list[dict]) -> tuple[str, dict]:
        query = """
        UNWIND $rows AS row

        MATCH (mc:MusicCatalog {track_id: row.track_id})
        MATCH (y:ReleaseYear {year: row.year})
        MERGE (mc)-[:RELEASED_IN]->(y)
        """

        parameters = {
            "rows": [
                {"track_id": track_id, "year": year}
                for row in rows
                if (track_id := Query._clean(row.get("track_id"))) is not None
                and (year := extract_release_year(row.get("track_album_release_date"))) is not None
            ]
        }
        return query, parameters

    @staticmethod
    def edge_has_genre_subgenre(rows: list[dict]) -> tuple[str, dict]:
        query = """
        UNWIND $rows AS row

        MATCH (g:Genre {genre: row.genre})
        MATCH (sg:SubGenre {subgenre: row.subgenre})
        MERGE (g)-[:GENRE_INCLUDES_SUBGENRE]->(sg)
        """

        parameters = {
            "rows": [
                {"genre": genre, "subgenre": subgenre}
                for row in rows
                if (genre := Query._clean(row.get("genres"))) is not None
                and (subgenre := Query._clean(row.get("subgenres"))) is not None
            ]
        }
        return query, parameters

    @staticmethod
    def _clean(value) -> str | None:
        value = scalar_or_none(value)
        if value is None:
            return None

        text = str(value).strip()
        return text or None

    @staticmethod
    def _clean_unique(values: list[str]) -> list[str]:
        return sorted({
            cleaned
            for value in values
            if (cleaned := Query._clean(value)) is not None
        })

    @staticmethod
    def _track_value_rows(
        rows: list[dict],
        source_column: str,
        target_key: str,
    ) -> list[dict]:
        return [
            {"track_id": track_id, target_key: value}
            for row in rows
            if (track_id := Query._clean(row.get("track_id"))) is not None
            and (value := Query._clean(row.get(source_column))) is not None
        ]

############################################ 서브노드 간 엣지 연결 #########################################

    @staticmethod
    def edge_has_genre_subgenre(rows: list[dict]) -> tuple[str, dict]:
        """
        genre_subgenre.csv(genres, subgenres) 행을 이용해
        기존 Genre·SubGenre 노드를 매칭하고, 서브장르가 해당 장르에 속함을 표시한다.
        """

        query = """
        UNWIND $rows AS row

        MATCH (g:Genre {genre: row.genre})
        MATCH (sg:SubGenre {subgenre: row.subgenre})

        MERGE (g)-[:GENRE_INCLUDES_SUBGENRE]->(sg)
        """

        merged_rows = []
        for row in rows:
            genre = scalar_or_none(row.get("genres"))
            subgenre = scalar_or_none(row.get("subgenres"))
            if genre is None or subgenre is None:
                continue
            merged_rows.append(
                {
                    "genre": str(genre).strip(),
                    "subgenre": str(subgenre).strip(),
                }
            )

        parameters = {"rows": merged_rows}

        return query, parameters


############################################ 시나리오 분류 (music_catalog_scenarios.csv) ############################################

    @staticmethod
    def scenario_dim_values_merge(dimension: str, rows: list[dict]) -> tuple[str, dict]:
        """
        지정한 dim_* 컬럼에 대응하는 노드 라벨로, 유일한 tag_id 값마다 노드를 MERGE한다.
        rows: { "tag_id": "weather_sunny" } 형태. dimension은 SCENARIO_DIM_TO_LABEL_AND_REL 키.
        """

        node_label, _ = SCENARIO_DIM_TO_LABEL_AND_REL[dimension]
        label = node_label.value
        query = f"""
        UNWIND $rows AS row
        MERGE (v:{label} {{name: row.tag_id}})
        SET v.tag_id = row.tag_id
        """
        parameters = {"rows": rows}
        return query, parameters

    @staticmethod
    def scenario_dim_link(dimension: str, rows: list[dict]) -> tuple[str, dict]:
        """
        MusicCatalog(track_id)와 해당 차원의 값 노드를 차원별 HAS_DIM_* 관계로 연결한다.
        rows: { "track_id", "tag_id" } 형태.
        """

        node_label, rel_type = SCENARIO_DIM_TO_LABEL_AND_REL[dimension]
        label = node_label.value
        rel = rel_type.value
        mcl = KagNodeLabel.MUSIC_CATALOG.value
        query = f"""
        UNWIND $rows AS row
        MATCH (mc:{mcl} {{track_id: row.track_id}})
        MATCH (v:{label} {{name: row.tag_id}})
        MERGE (mc)-[:{rel}]->(v)
        """
        parameters = {"rows": rows}
        return query, parameters