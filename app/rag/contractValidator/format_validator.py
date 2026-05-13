"""
# 형식 및 스키마 검증
- 데이터가 시스템이 이해할 수 있는 올바른 형식(JSON, PDF 구조 등)인지 확인합니다.

함수 : check_required_fields(contract_data)	
설명 : 필수 계약 항목(당사자, 일자, 금액 등)의 누락 여부 확인	
Input : 추출된 계약 데이터 객체	
Output : 형식 일치 여부 결과

함수 : validate_data_types(contract_data)	
설명 : 날짜 형식이나 숫자 단위가 올바른지 확인	
Input : 계약 데이터 객체	
Output :타입 유효성 결과
"""