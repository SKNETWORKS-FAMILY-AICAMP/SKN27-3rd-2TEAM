# 로그
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 패키지
import pandas as pd
from pathlib import Path
from common.connection import Neo4j_Connection


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
def import_data(path: str = None, query_params=None):
    """ CSV 각 행에 대해 query_params(row)로 얻은 Cypher·파라미터를 실행해 그래프 DB에 적재한다. """

    df = pd.read_csv(get_filepath(path))
    driver = Neo4j_Connection()

    for i, row in df.iterrows():
        query, parameters = query_params(row)
        driver.execute_query(query=query, parameters=parameters)
        logger.info(i)
    
    logger.info(f'데이터 {df.shape[0]}개 적재 완료!')
