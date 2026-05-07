# 로그
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 패키지
import pandas as pd
from pathlib import Path
from common.connection import Neo4j_Connection
from common.querys import Query


####################################################################
# 파일 경로 반환 함수 
####################################################################
def get_filepath(file_name:str) -> str:
    """ 파일 이름을 넣었을 때 data 폴더 경로의 이름을 반환하는 함수 """
    _DATA_DIR = Path(__file__).resolve().parent / "data"
    return _DATA_DIR / file_name



####################################################################
# 쿼리 실행 함수 
####################################################################
def import_data(path:str=None, query:Query=None):
    """ users 데이터를 그래프 db에 적제하는 함수 """

    # 데이터 로드 / 드라이버 생성 
    df = pd.read_csv(get_filepath(path))
    driver = Neo4j_Connection()

    for _, row in df.iterrows():
        query, parameters = query(row)
        driver.execute_query(query=query, parameters=parameters)
        logger.info(_)
    
    logger.info(f'데이터 {df.shape[0]}개 적재 완료!')
