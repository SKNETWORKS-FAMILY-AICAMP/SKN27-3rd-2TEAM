"""
# 구체적인 처리 로직
- 상태를 입력받아 특정 작업을 수행하고 상태를 업데이트하는 개별 작업 단위입니다.

공통 Input	Output
Input : RagState (현재까지의 상태)
Output : RagState (업데이트된 상태)

함수 : retrieve_documents(state)
설명 : 질문에 관련된 지식을 벡터 DB에서 검색

함수 : generate_answer(state)
설명 : 검색된 컨텍스트와 질문을 바탕으로 LLM을 통해 답변 생성

함수 : grade_documents(state)
설명 : 검색된 문서들이 질문과 관련 있는지 평가 및 필터링

함수 : transform_query(state)
설명 : 검색 결과가 부실할 경우 질문을 더 나은 형태로 재작성
"""