"""
# 쿼리와 가장 유사한 문서 조각을 검색하고, 검색 결과의 순위를 재정렬하여 정확도를 향상합니다.

함수 : retrieve_relevant_docs(query, k)
설명 : 쿼리와 가장 유사한 k개의 문서 조각을 검색
Input : 사용자 질문(Query), 검색 개수(k)
Output : 검색된 관련 문서 리스트

함수 : rerank_documents(query, docs)
설명: 검색된 결과의 순위를 재정렬하여 정확도 향상
Input : 질문, 문서 리스트
Output : 재정렬된 문서 리스트
"""