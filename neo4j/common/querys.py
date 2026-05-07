# 로그
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 패키지
import pandas as pd


####################################################################
# 실행할 쿼리 목록 정의
####################################################################
class Query:
    """CSV 한 행(pandas Series)마다 노드 적재용 query와 파라미터를 반환한다.
    import_data(..., row_query=Query.<메서드>)처럼 콜러블을 넘긴다.

    참고: @property는 row 인자를 받을 수 없어 @staticmethod로 둔다.
    """

    @staticmethod
    def users(row: pd.Series):
        query = """
        MERGE (u:User {user_id: $user_id})
        SET u.display_name = $display_name
        """
        parameters = {
            "user_id": str(row["user_id"]),
            "display_name": row["display_name"],
        }
        return query, parameters

    @staticmethod
    def genres(row: pd.Series):
        query = """
        MERGE (g:Genre {genre: $genre})
        """
        parameters = {"genre": row["genre"]}
        return query, parameters

    @staticmethod
    def artists(row: pd.Series):
        query = """
        MERGE (a:Artist {artist: $artist})
        """
        parameters = {"artist": row["artist"]}
        return query, parameters

    @staticmethod
    def moods(row: pd.Series):
        query = """
        MERGE (m:Mood {mood: $mood})
        """
        parameters = {"mood": row["mood"]}
        return query, parameters
