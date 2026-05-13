import csv
import os
from glob import glob

# 스크립트 실행 위치 기준 data 폴더 경로 설정
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, "..", "data")

# embedded_data 로 시작하는 모든 CSV 파일 검색 (단일 파일, 분할 파일 모두 포함)
files = glob(os.path.join(data_dir, "embedded_data_part*.json"))

if not files:
    print(f"'{data_dir}' 폴더 내에 embedded_data.csv 또는 part 파일이 없습니다.")
    exit()

total_rows = 0

print("=== 분할된 CSV 파일별 저장된 데이터(행) 개수 ===")
for file in sorted(files):
    with open(file, mode='r', encoding='utf-8-sig', errors='ignore') as f:
        reader = csv.reader(f)
        try:
            # 헤더 행 건너뛰기
            next(reader)
            # 나머지 데이터 행의 개수 합산
            row_count = sum(1 for row in reader)
            total_rows += row_count
            filename = os.path.basename(file)
            print(f" - {filename:<25} : {row_count}개")
        except StopIteration:
            filename = os.path.basename(file)
            print(f" - {filename:<25} : 0개 (빈 파일)")

print("-" * 40)
print(f"▶ 총 누적 임베딩 완료 개수: {total_rows}개")
