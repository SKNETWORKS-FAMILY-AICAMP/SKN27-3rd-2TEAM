# 로그
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 패키지
import pandas as pd

# 모듈 
from app.kag.connection import Neo4j_Connection


####################################################################
# 실행할 쿼리 목록 정의
####################################################################
class KagCypherQuery:
    """KAG Cypher Query 목록 정의"""

    @staticmethod
    def user_info(row: dict) -> tuple[str, dict, str]: # tuple[str, dict]
        """ 
        지정한 사용자의 이름을 조회하는 쿼리 
        [input]
        {user_id : 사용자 ID}

        [output]
        {display_name : 사용자 이름}
        """

        similar_request = "특정 ID의 사용자 이름을 알려주세요."

        query = """
        MATCH (u:User {user_id: $user_id})
        RETURN u.display_name AS display_name
        """

        parameters = {
            "user_id": row["user_id"],
        }
        return query, parameters, similar_request









if __name__ == "__main__":
    # 테스트 코드
    conn = Neo4j_Connection()

    # => 조회할 사용자 정보 셋업 (user_info는 row dict 필요)
    row = {"user_id": "user_001"}
    query, parameters, similar_request = KagCypherQuery.user_info(row)
    logger.info("===요청한 정보===")
    logger.info(query)
    logger.info(parameters)
    logger.info(similar_request)

    # => 조회 쿼리 요청
    result = conn.execute_query(query, parameters)
    logger.info("===조회 결과===")
    logger.info(f"result: {result}\nsimilar_request: {similar_request}")