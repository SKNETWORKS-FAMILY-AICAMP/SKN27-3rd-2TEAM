"""
검색된 지식과 질문을 결합하여 최적의 프롬프트를 구성하고, LLM을 호출해 최종 답변을 생성합니다.

함수 : construct_prompt(context, question)
설명 : 검색된 지식과 질문을 결합하여 최적의 프롬프트 구성
Input : 검색 결과(Context), 질문
Output : 최적화된 프롬프트 문자열

함수 : invoke_llm(prompt)
설명 : LLM을 호출하여 최종 답변 생성
Input : 프롬프트 문자열
Output : 생성된 최종 텍스트 답변
"""

