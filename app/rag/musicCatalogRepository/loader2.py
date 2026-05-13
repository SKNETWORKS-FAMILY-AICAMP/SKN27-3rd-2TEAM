import os
import csv
import json
from glob import glob
from tqdm import tqdm
from langchain_ollama import OllamaEmbeddings
from sql_repostiory import es_client

# 스크립트 실행 위치와 무관하게 절대 경로 지정
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, "..", "data")

# 1. 대상 CSV 파일 찾기
files = glob(os.path.join(data_dir, "spotify_songs.csv"))
print(f"전체 csv 파일의 수: {len(files)}")

if not files:
    print("처리할 CSV 파일이 없습니다.")
    exit()

# 처리할 대상 파일
input_csv_path = files[0]
print(f"처리할 파일: {input_csv_path}")

# 2. Embedding Model 설정
embeddings = OllamaEmbeddings(model="qwen3-embedding:0.6b")

output_csv_path = os.path.join(data_dir, "embedded_data.csv")
batch_size = 1 # 배치 사이즈는 1 이상이어야 합니다.

# 3. 입력 데이터 읽기 (원본 컬럼 유지 및 각 컬럼별 임베딩 컬럼 추가)
with open(input_csv_path, mode='r', encoding='utf-8-sig', errors='ignore') as infile:
    reader = csv.DictReader(infile)
    if reader.fieldnames is None:
        print("CSV 파일에 헤더가 없습니다.")
        exit()
        
    original_cols = list(reader.fieldnames)
    # 각 컬럼에 대해 text와 embedding 컬럼 생성
    fieldnames = []
    for col in original_cols:
        fieldnames.append(f"{col}_text")
        fieldnames.append(f"{col}_embedding")
        
    rows = list(reader)

print(f"로드된 전체 행의 수: {len(rows)}")

# 4. 재시작 및 파일 분할(Chunk) 설정
start_index = 0  # 시작 인덱스
end_index = 15999  # 종료 인덱스 (포함)
chunk_size = 500   # 파일 하나의 크기가 너무 커지는 것을 막기 위해 500개 행마다 새로운 CSV 파일 생성

print(f"임베딩 결과를 {chunk_size}개 단위로 분할하여(embedded_data_partX.csv) 저장합니다...")
print("전체 문서 임베딩을 시작합니다...")
emb_vectors_count = 0

# tqdm에 initial 값을 주어 진행률 바가 이어서 진행되도록 표시
total_items = min(end_index + 1, len(rows))
for i in tqdm(range(start_index, total_items, batch_size), desc="임베딩 진행률", initial=start_index, total=total_items):
    batch_rows = rows[i:i+batch_size]
    
    # 현재 저장될 파일의 인덱스 계산 (예: 1947번 데이터는 1947 // 500 = 3 => part3.csv 에 저장)
    current_part = i // chunk_size
    current_output_csv = os.path.join(data_dir, f"embedded_data_part{current_part}.csv")
    
    # 해당 분할 파일이 존재하지 않으면 새로 만들고 헤더를 가장 먼저 작성
    if not os.path.exists(current_output_csv):
        with open(current_output_csv, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
    # 이번 배치의 모든 행에서 '모든 컬럼의 개별 값'을 순서대로 추출
    texts_to_embed = []
    for row in batch_rows:
        for col in original_cols:
            # 빈 문자열이라도 임베딩을 수행하도록 처리 (에러 방지)
            val = str(row[col]).strip()
            if not val:
                val = " "
            texts_to_embed.append(val)
            
    # 배치 단위로 임베딩 수행 (Ollama 타임아웃 등 에러 대응)
    try:
        batch_emb = embeddings.embed_documents(texts_to_embed)
    except Exception as e:
        print(f"\n임베딩 처리 중 오류 발생 (인덱스 {i}): {e}")
        continue
        
    emb_vectors_count += len(batch_emb)
    
    # 임베딩 결과를 원래 텍스트와 함께 새로운 매핑 구조로 저장
    new_batch_rows = []
    idx = 0
    for row in batch_rows:
        new_row = {}
        for col in original_cols:
            val = str(row[col]).strip()
            if not val:
                val = " "
            new_row[f"{col}_text"] = val
            new_row[f"{col}_embedding"] = json.dumps(batch_emb[idx])
            idx += 1
        new_batch_rows.append(new_row)
        
    # 현재 해당하는 분할 CSV 파일에 누적(append) 저장
    with open(current_output_csv, mode='a', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerows(new_batch_rows)
        
    # Python 메모리 최적화: 매 반복마다 큰 객체 명시적 삭제
    del texts_to_embed
    del batch_emb

print(f"생성된 임베딩 벡터의 총 수: {emb_vectors_count}")
print("전체 CSV 파일 저장 완료.")

# # 인덱스 이름
# index_name = "rag_keywords"

# # 기존 인덱스 삭제 (있다면)
# if es_client.indices.exists(index=index_name):
#     es_client.indices.delete(index=index_name)
#     print(f"기존 인덱스 '{index_name}' 삭제")

# # 벡터 인덱스 매핑 생성 (qwen3-embedding:0.6b는 1024차원)
# index_mapping = {
#     "mappings": {
#         "properties": {
#             "text": {
#                 "type": "text",
#                 "analyzer": "standard"
#             },
#             "embedding": {
#                 "type": "dense_vector",
#                 "dims": len(emb_vectors),  # 임베딩 차원 (모델에 따라 조정)
#                 "index": True,
#                 "similarity": "cosine"  # 코사인 유사도
#             },
#             "metadata": {
#                 "type": "object",
#                 "enabled": True
#             }
#         }
#     }
# }

# # 인덱스 생성
# es_client.indices.create(index=index_name, body=index_mapping)
# print(f"인덱스 '{index_name}' 생성 완료")
