"""
SQLAlchemy / Django ORM을 사용한 실제 DB 세션 처리 및 Elasticsearch 연동 구현체입니다.

함수 : Elasticsearch 데이터 조회
설명 : Elasticsearch에서 데이터를 가져오는 로직
Input : 쿼리 파라미터
Output :검색 결과 데이터


함수 : ORM 세션 처리
설명: SQLAlchemy / Django ORM을 사용한 실제 DB 세션 처리
Input : DB 연결 정보
Output : DB 세션 객체


함수 : Music ⋈ Contract JOIN 조회	
설명 : Music 테이블과 Contract 테이블을 Join하여 데이터를 가져오는 구체적인 로직
Input : 조인 조건
Output : 결합된 레코드 결과

"""
# elasticsearch 연결
from elasticsearch import Elasticsearch
import warnings

# SSL 경고 무시 (개발 환경용)
warnings.filterwarnings('ignore')

# Elasticsearch 클라이언트 생성
# elasticsearch 9.x는 명시적인 scheme 지정이 필요합니다
try:
    es_client = Elasticsearch(
        ["http://localhost:9200"],  # 리스트 형태로, scheme 포함
        basic_auth=("elastic", "changeme123!"),  # 인증 정보 (보안 활성화 시 필수)
        verify_certs=False,
        ssl_show_warn=False,
        request_timeout=30,
        max_retries=3,
        retry_on_timeout=True,
        # 호환성 헤더 비활성화 (개발 환경용)
        headers={"accept": "application/json", "content-type": "application/json"}
    )
    
    # 연결 확인
    if es_client.ping():
        print("Elasticsearch 연결 성공!")
        print()
        
        # 클러스터 정보
        info = es_client.info()
        print(f"버전: {info['version']['number']}")
        print(f"클러스터 이름: {info['cluster_name']}")
        print(f"노드 이름: {info['name']}")
        print()
        print(f"Elasticsearch URL: http://localhost:9200")
    else:
        print("Elasticsearch 연결 실패 (ping 실패)")
        
except Exception as e:
    print("Elasticsearch 연결 중 오류 발생:")
    print(f"   에러 타입: {type(e).__name__}")
    print(f"   에러 메시지: {str(e)}")

import pandas as pd
import json
from elasticsearch import helpers

def init_elasticsearch_index(index_name="spotify_songs"):
    """Elasticsearch 인덱스를 생성하고 매핑을 설정합니다."""
    # 기존 인덱스가 있다면 삭제
    if es_client.indices.exists(index=index_name):
        es_client.indices.delete(index=index_name)
        print(f"기존 인덱스 '{index_name}' 삭제")
        
    index_mapping = {
        "mappings": {
            "properties": {
                "content": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "embedding": {
                    "type": "dense_vector",
                    "dims": 1024,
                    "index": True,
                    "similarity": "cosine",
                },
                "metadata": {
                    "type": "object",
                    "enabled": True,
                },
            }
        }
    }
    es_client.indices.create(index=index_name, body=index_mapping)
    print(f"인덱스 '{index_name}' 생성 완료")

def ingest_json_to_elasticsearch(json_path, index_name="spotify_songs"):
    """JSON 데이터를 읽어서 Elasticsearch에 벌크 인서트합니다."""
    print(f"\nJSON 파일 읽는 중: {json_path}")
    
    actions = []
    with open(json_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            try:
                row = json.loads(line)
            except Exception as e:
                print(f"JSON 파싱 실패: {e}")
                continue
            
            # JSONL에서는 embedding이 이미 리스트 형태로 저장되어 있음
            embedding_list = row.get('embedding', [])
            content = row.get('content', '')
            
            # content와 embedding을 제외한 모든 필드를 metadata에 동적으로 추가
            metadata = {}
            for k, v in row.items():
                if k not in ['content', 'embedding']:
                    metadata[k] = v
                    
            # 문서 구조 구성
            doc = {
                "_index": index_name,
                "_source": {
                    "content": content,
                    "embedding": embedding_list,
                    "metadata": metadata
                }
            }
            actions.append(doc)
    
    if not actions:
        print("삽입할 데이터가 없습니다.")
        return

    print(f"총 {len(actions)}개의 문서를 Elasticsearch '{index_name}' 인덱스에 삽입합니다...")
    try:
        success, failed = helpers.bulk(es_client, actions)
        print(f"데이터 삽입 완료! 성공: {success}, 실패: {failed}")
    except Exception as e:
        print(f"벌크 인서트 중 오류 발생: {e}")

if __name__ == "__main__":
    import glob
    import os
    
    data_dir = r"C:\workspace\dev\project\SKN27-3rd-2TEAM\app\rag\data"
    index_name = "spotify_songs"
    
    init_elasticsearch_index(index_name)
    
    search_pattern = os.path.join(data_dir, "embedded_data_part*.json")
    json_files = glob.glob(search_pattern)
    
    json_files.sort()
    
    if not json_files:
        print(f"'{search_pattern}' 경로에서 JSON 파일을 찾을 수 없습니다.")
    else:
        print(f"총 {len(json_files)}개의 JSON 파일을 발견했습니다. 순차적으로 적재를 시작합니다...\n")
        for json_file_path in json_files:
            ingest_json_to_elasticsearch(json_file_path, index_name)
            
        print("\n모든 JSON 파일의 데이터 적재가 완료되었습니다!")
