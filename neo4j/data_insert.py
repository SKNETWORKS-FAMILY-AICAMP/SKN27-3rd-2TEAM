# 로그 
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 모듈
from common.querys import Query
from common.utils import import_data
from common.connection import Neo4j_Connection


###################################################################################################
# 메인 함수 정의 (실행할 쿼리 함수 선언)
###################################################################################################
def main():
    """ 해당 부분에 사전에 정의한 쿼리 함수들을 설정해서 실행함 """
    # 모든 데이터 삭제 (초기화) 
    conn = Neo4j_Connection()
    conn.clear_database()

    # 유저 데이터 추가 
    import_data(path="users.csv", row_query=Query.users)
    import_data(path="genres.csv", row_query=Query.genres)
    import_data(path="artists.csv", row_query=Query.artists)
    import_data(path="moods.csv", row_query=Query.moods)


















###################################################################################################
# 메인 함수 실행 
###################################################################################################
if __name__ == '__main__':
    main()
