"""
원본 문서를 청킹(Chunking)하고 메타데이터를 추출하여 저장 준비합니다.

함수 : process_and_index(raw_data)
설명 : 원본 문서를 청킹하고 메타데이터를 추출하여 저장 준비
Input : PDF, 텍스트 파일 등의 원본 데이터
Output : 인덱싱 완료 상태 및 문서 ID

함수 : update_index(document_id, new_data)
설명 : 기존 인덱싱된 데이터를 수정
Input : 문서 ID, 수정 데이터
Output : 업데이트된 인덱스 상태

"""