# 로그 
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 모듈
from common.querys import Query
from common.utils import import_data, import_column, execute_query
from common.connection import Neo4j_Connection
from common.constant import KagMoodLabel, KagTempoLabel


###################################################################################################
# 메인 함수 정의 (실행할 쿼리 함수 선언)
###################################################################################################
def main():
    """ 
    해당 부분에 사전에 정의한 쿼리 함수들을 설정해서 실행함 
    작업에 필요한 부분이 있으면 해당 부분만 주석 해제해서 실행하면 된다. 
    """
    ######################## 모든 데이터 삭제 (초기화) ##############################
    # conn = Neo4j_Connection()
    # conn.clear_database()


    ######################## 음원 데이터 전체 추가 (약 3만개) ##############################
    # import_data(path="music_catalog.csv", query_params=Query.music_catalog)


    ######################## 엣지 연결할 추가 노드 적제 ##############################
    # import_column(path="music_catalog.csv", column_name="playlist_genre", query_params=Query.genres)
    # import_column(path="music_catalog.csv", column_name="track_artist", query_params=Query.artists)
    # import_column(path="music_catalog.csv", column_name="playlist_subgenre", query_params=Query.subgenres)
    # import_column(path="music_catalog.csv", column_name="track_album_release_date", query_params=Query.year)
    # execute_query(values=list(KagMoodLabel.__members__.values()), query_params=Query.mood)
    # execute_query(values=list(KagTempoLabel.__members__.values()), query_params=Query.tempo)


    ############################### 엣지 연결 ############################################
    # 데이터 전체를 주회해야 하므로 import_data 를 통해 실행하게 됨 
    # 다만 각 쿼리 내부에 연결 여부를 매핑하는 함수가 들어있어야 한다. 조건에 맞으면 연결 / 아니면 pass 
    import_data(path="music_catalog.csv", query_params=Query.edge_has_genre)












###################################################################################################
# 메인 함수 실행 
###################################################################################################
if __name__ == '__main__':
    main()
