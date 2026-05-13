import numpy as np
from langchain_ollama import OllamaEmbeddings

# 임베딩 모델 설정
EMBEDDING_MODEL_NAME = "qwen3-embedding:0.6b"

def get_embeddings(text_or_list):
    """
    텍스트를 고차원 벡터로 변환합니다.
    Input : 텍스트 리스트 또는 단일 쿼리
    Output : 벡터 데이터 (List[float] 또는 List[List[float]])
    """
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)
    
    if isinstance(text_or_list, str):
        return embeddings.embed_query(text_or_list)
    else:
        return embeddings.embed_documents(text_or_list)

def calculate_similarity(vec1, vec2):
    """
    두 벡터 간의 코사인 유사도를 계산합니다.
    Input : 벡터 두 개
    Output : 유사도 점수 (float)
    """
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
        
    return float(dot_product / (norm_v1 * norm_v2))