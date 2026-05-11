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
)


####################################################################
# 실행할 쿼리 목록 정의
####################################################################
class Query:
    """CSV 한 행(pandas Series)마다 노드 적재용 query와 파라미터를 반환한다.
    import_data(..., row_query=Query.<메서드>)처럼 콜러블을 넘긴다.

    참고: @property는 row 인자를 받을 수 없어 @staticmethod로 둔다.
    """

    @staticmethod
    def music_catalog(rows: list[dict]) -> tuple[str, dict]:
        """
        Kaggle/Spotify 포맷 music_catalog.csv 데이터를
        UNWIND 기반으로 MusicCatalog 노드에 적재한다.
        """

        query = """
        UNWIND $rows AS row

        MERGE (mc:MusicCatalog {track_id: row.track_id})

        SET mc.name = row.track_name,
            mc.track_id = row.track_id,
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
                    "track_name": scalar_or_none(row["track_name"]),
                    "track_artist": scalar_or_none(row["track_artist"]),
                    "track_popularity": scalar_or_none(row["track_popularity"]),
                    "track_album_id": scalar_or_none(row["track_album_id"]),
                    "track_album_name": scalar_or_none(row["track_album_name"]),
                    "track_album_release_date": scalar_or_none(row["track_album_release_date"]),
                    "playlist_name": scalar_or_none(row["playlist_name"]),
                    "playlist_id": scalar_or_none(row["playlist_id"]),
                    "playlist_genre": scalar_or_none(row["playlist_genre"]),
                    "playlist_subgenre": scalar_or_none(row["playlist_subgenre"]),
                    "danceability": scalar_or_none(row["danceability"]),
                    "energy": scalar_or_none(row["energy"]),
                    "key": scalar_or_none(row["key"]),
                    "loudness": scalar_or_none(row["loudness"]),
                    "mode": scalar_or_none(row["mode"]),
                    "speechiness": scalar_or_none(row["speechiness"]),
                    "acousticness": scalar_or_none(row["acousticness"]),
                    "instrumentalness": scalar_or_none(row["instrumentalness"]),
                    "liveness": scalar_or_none(row["liveness"]),
                    "valence": scalar_or_none(row["valence"]),
                    "tempo": scalar_or_none(row["tempo"]),
                    "duration_ms": scalar_or_none(row["duration_ms"]),
                }
                for row in rows
            ]
        }

        return query, parameters

############################################ 컬럼별 노드 적제 ############################################

    @staticmethod
    def genres(values: list[str]) -> tuple[str, dict]:
        query = """
        UNWIND $values AS value
        MERGE (:Genre {genre: value})
        """
        parameters = {"values": values}
        return query, parameters

    @staticmethod
    def artists(values: list[str]) -> tuple[str, dict]:
        query = """
        UNWIND $values AS value
        MERGE (:Artist {artist: value})
        """
        parameters = {"values": values}
        return query, parameters

    @staticmethod
    def subgenres(values: list[str]) -> tuple[str, dict]:
        query = """
        UNWIND $values AS value
        MERGE (:SubGenre {subgenre: value})
        """
        parameters = {"values": values}
        return query, parameters

    @staticmethod
    def year(values: list[str | None]) -> tuple[str, dict]:
        query = """
        UNWIND $years AS year
        MERGE (:ReleaseYear {year: year})
        """

        years = [
            extract_release_year(value)
            for value in values
            if extract_release_year(value) is not None
        ]

        parameters = {"years": list(set(years))}
        return query, parameters

    @staticmethod
    def mood(values: list[KagMoodLabel | str]) -> tuple[str, dict]:
        query = """
        UNWIND $values AS value
        MERGE (:Mood {mood: value})
        """

        mood_values = [
            value.value if isinstance(value, KagMoodLabel) else str(value)
            for value in values
        ]

        parameters = {"values": list(set(mood_values))}
        return query, parameters

    @staticmethod
    def tempo(values: list[KagTempoLabel | str]) -> tuple[str, dict]:
        query = """
        UNWIND $values AS value
        MERGE (:Tempo {tempo: value})
        """

        tempo_values = [
            value.value if isinstance(value, KagTempoLabel) else str(value)
            for value in values
        ]

        parameters = {"values": list(set(tempo_values))}
        return query, parameters



############################################ 데이터 엣지 연결 ############################################

    @staticmethod
    def edge_has_genre(rows: list[dict]) -> tuple[str, dict]:
        """
        기존 MusicCatalog 노드와 기존 Genre 노드를
        UNWIND 기반으로 연결하는 쿼리.
        """

        query = """
        UNWIND $rows AS row

        MATCH (mc:MusicCatalog {track_id: row.track_id})
        MATCH (g:Genre {genre: row.genre})

        MERGE (mc)-[:HAS_GENRE]->(g)
        """

        parameters = {
            "rows": [
                {
                    "track_id": str(row["track_id"]),
                    "genre": row["playlist_genre"],
                }
                for row in rows
            ]
        }

        return query, parameters

    @staticmethod
    def edge_has_subgenre(rows: list[dict]) -> tuple[str, dict]:
        """
        기존 MusicCatalog 노드와 기존 SubGenre 노드를
        UNWIND 기반으로 연결하는 쿼리.
        """

        query = """
        UNWIND $rows AS row

        MATCH (mc:MusicCatalog {track_id: row.track_id})
        MATCH (sg:SubGenre {subgenre: row.subgenre})

        MERGE (mc)-[:HAS_SUBGENRE]->(sg)
        """

        parameters = {
            "rows": [
                {
                    "track_id": str(row["track_id"]),
                    "subgenre": row["playlist_subgenre"],
                }
                for row in rows
                if row.get("track_id") is not None
                and row.get("playlist_subgenre") is not None
            ]
        }

        return query, parameters

    @staticmethod
    def edge_performed_by(rows: list[dict]) -> tuple[str, dict]:
        """
        기존 MusicCatalog 노드와 기존 Artist 노드를
        UNWIND 기반으로 연결하는 쿼리.
        """

        query = """
        UNWIND $rows AS row

        MATCH (mc:MusicCatalog {track_id: row.track_id})
        MATCH (a:Artist {artist: row.artist})

        MERGE (mc)-[:PERFORMED_BY]->(a)
        """

        parameters = {
            "rows": [
                {
                    "track_id": str(row["track_id"]),
                    "artist": row["track_artist"],
                }
                for row in rows
                if row.get("track_id") is not None
                and row.get("track_artist") is not None
            ]
        }

        return query, parameters





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
    def scenario_dim_tags_merge(rows: list[dict]) -> tuple[str, dict]:
        """
        dim_* 컬럼에서 등장하는 (컬럼명, tag_id) 쌍별로 ScenarioTag 노드를 MERGE한다.
        rows: { "dimension": "dim_weather", "tag_id": "weather_sunny" } 형태.
        """

        label = KagNodeLabel.SCENARIO_TAG.value
        query = f"""
        UNWIND $rows AS row
        MERGE (st:{label} {{
            dimension: row.dimension,
            tag_id: row.tag_id
        }})
        """
        parameters = {"rows": rows}
        return query, parameters

    @staticmethod
    def scenario_dim_tags_link(rows: list[dict]) -> tuple[str, dict]:
        """
        MusicCatalog(track_id)와 ScenarioTag(dimension, tag_id)를 HAS_SCENARIO_TAG로 연결한다.
        rows: { "track_id", "dimension", "tag_id" } 형태. 해당 MusicCatalog 노드가 없으면 해당 행은 매칭되지 않는다.
        """

        rel = KagRelationType.HAS_SCENARIO_TAG.value
        mcl = KagNodeLabel.MUSIC_CATALOG.value
        stl = KagNodeLabel.SCENARIO_TAG.value
        query = f"""
        UNWIND $rows AS row
        MATCH (mc:{mcl} {{track_id: row.track_id}})
        MATCH (st:{stl} {{dimension: row.dimension, tag_id: row.tag_id}})
        MERGE (mc)-[:{rel}]->(st)
        """
        parameters = {"rows": rows}
        return query, parameters