"""
# 비즈니스 로직 검증
- 계약 내용이 법적·사업적 정책이나 기존 데이터와 모순되지 않는지 확인합니다.

함수 : verify_contract_period(start_date, end_date)
설명 : 시작일이 종료일보다 앞서는지 등 기간 논리 확인
Input : 시작일, 종료일
Output : 기간 논리 타당성 결과

함수 : cross_check_with_db(contract_info)
설명 : 기존 등록 계약과 중복·충돌 조건이 있는지 DB 연동 확인
Input : 계약 상세 정보 및 DB 조회 데이터
Output : 로직 타당성 결과 및 위반 내역 리포트

함수 : check_compliance_rules(text)
설명 : 필수 문구나 금지 조항이 포함되었는지 검사
Input : 계약서 텍스트
Output : 컴플라이언스 통과 여부
"""