from elasticsearch import Elasticsearch
from app.rag.services.embedding import get_embeddings
import warnings

# SSL 경고 무시
warnings.filterwarnings('ignore')

# Elasticsearch 클라이언트 설정
# (sql_repostiory.py의 설정을 참조하였습니다)
ES_URL = "http://localhost:9200"
ES_USER = "elastic"
ES_PW = "changeme123!"
INDEX_NAME = "spotify_songs"

try:
    es_client = Elasticsearch(
        [ES_URL],
        basic_auth=(ES_USER, ES_PW),
        verify_certs=False,
        ssl_show_warn=False,
    )
except Exception as e:
    print(f"Elasticsearch 연결 오류: {e}")
    es_client = None

def retrieve_relevant_docs(query: str, k: int = 5, search_type: str = "hybrid"):
    """
    Elasticsearch에서 쿼리와 가장 관련 있는 문서를 검색합니다.
    
    Input : 
        - query : 사용자 질문 또는 키워드
        - k : 검색할 문서 개수
        - search_type : 'lexical' (키워드), 'semantic' (벡터), 'hybrid' (복합)
    Output : 
        - 검색된 문서 리스트 (내용, 메타데이터, 유사도 점수 포함)
    """
    if not es_client:
        return []

    # 1. 벡터 검색을 위한 임베딩 생성
    query_vector = get_embeddings(query)

    search_body = {
        "size": k,
        "query": {},
    }

    if search_type == "lexical":
        # 키워드 기반 검색 (BM25) - 주요 텍스트 필드들에서 검색 (날짜/숫자 필드 제외)
        search_body["query"] = {
            "multi_match": {
                "query": query,
                "fields": [
                    "content", 
                    "metadata.song", 
                    "metadata.Artist(s)", 
                    "metadata.Genre", 
                    "metadata.emotion", 
                    "metadata.Album",
                    "metadata.text"
                ]
            }
        }
    
    elif search_type == "semantic":
        # 벡터 기반 유사도 검색 (KNN)
        search_body = {
            "size": k,
            "knn": {
                "field": "embedding",
                "query_vector": query_vector,
                "k": k,
                "num_candidates": 100
            }
        }
        
    else: # hybrid
        # 키워드와 벡터 검색 결합
        search_body = {
            "size": k,
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "content", 
                                    "metadata.song", 
                                    "metadata.Artist(s)", 
                                    "metadata.Genre", 
                                    "metadata.emotion", 
                                    "metadata.Album",
                                    "metadata.text"
                                ],
                                "boost": 0.3 # 가중치 조절
                            }
                        }
                    ]
                }
            },
            "knn": {
                "field": "embedding",
                "query_vector": query_vector,
                "k": k,
                "num_candidates": 100,
                "boost": 0.7 # 가중치 조절
            }
        }

    try:
        response = es_client.search(index=INDEX_NAME, body=search_body)
        hits = response['hits']['hits']
        
        results = []
        for hit in hits:
            results.append({
                "doc_id": hit['_source'].get('metadata', {}).get('doc_id', hit['_id']),
                "content": hit['_source'].get('content', ''),
                "metadata": hit['_source'].get('metadata', {}),
                "score": hit['_score'] # 유사도 점수
            })
        return results

    except Exception as e:
        print(f"검색 중 오류 발생: {e}")
        return []

def rerank_documents(query: str, docs: list):
    """
    검색된 결과의 순위를 재정렬합니다. 
    (현재는 점수 기반 정렬 상태를 유지하며, 추후 Cross-Encoder 등을 추가할 수 있습니다.)
    """
    # 기본적으로 Elasticsearch에서 점수 순으로 정렬되어 반환되지만,
    # 추가적인 로직이 필요할 경우 여기서 구현합니다.
    return sorted(docs, key=lambda x: x['score'], reverse=True)

# (retrieval.py 하단 수정)
if __name__ == "__main__":
    # 이 파일은 모듈로 호출되며, 실제 테스트는 app/rag/main-test.py에서 수행합니다.
    pass