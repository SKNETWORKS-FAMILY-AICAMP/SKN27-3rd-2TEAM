"""
모든 저장소 구현체가 따라야 할 공통 인터페이스를 정의합니다.


함수 : get_by_id(id)/	
설명 : ID로 레코드 조회/
Input :	레코드 ID/
Output : 단일 레코드

함수 : search_by_metadata(filters)
설명 :필터 조건으로 레코드 조회
Input : 필터 조건 객체	
Output : 조건 부합 레코드 리스트

함수 : list_all()
설명 : 전체 목록 조회
Input : -
Output : 전체 레코드 목록
"""