# 로그 
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 패키지
import pandas as pd


####################################################################
# 실행할 쿼리 목록 정의 
####################################################################
class Query():
    """ 
    쿼리 목록 정의, 각 쿼리는 내장함수의 실행 결과 값을 쿼리와 파라미터 값으로 반환해서 가지고 있음 \
    각각의 쿼리는 인자 처럼 선언하면 @property 데코레이터를 사용해서 클래스 속성으로 정의함
    호출하면 용도에 맞는 쿼리랑 파라미터 셋을 받아올 수 있게 설계됨 
    - 각 쿼리의 이름은 불러올 데이터 셋의 이름으로 결정 / 추가 용도가 있으면 파일 명 뒤에 postfix로 붙음 
    """
    

    @property
    def users(self, row:pd.Series=None):
        query = """
        MERGE (u:User {user_id: $user_id})
        SET u.display_name = $display_name
        """

        parameters = {
            "user_id": str(row["user_id"]),
            "display_name": row["display_name"],
        }

        return query, parameters