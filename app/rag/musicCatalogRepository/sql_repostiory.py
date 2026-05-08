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