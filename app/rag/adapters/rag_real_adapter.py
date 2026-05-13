"""
# 실제 구현체
- 실제 LangGraph·외부 엔진에 연결하고, OpenAI / Anthropic API 등 외부 인프라와의 통신을 처리합니다.
			
함수 : connect_langgraph(builder)
설명 : 실제 LangGraph나 외부 엔진에 연결하여 그래프 실행
Input : 서비스 계층에서 가공된 데이터
Output : 외부 엔진 Raw 응답 데이터

함수 : handle_external_api(payload)
설명 : 외부 API와의 통신을 처리
Input : API 페이로드	
Output : 외부 API 응답 데이터
"""