"""
# RAG 전용 환각 검증
- RAG 시스템에서 생성된 답변이 원본 계약서 내용에 충실한지(Faithfulness)를 검증합니다.
	
함수 : verify_grounding(answer, context)	
설명 : 생성된 답변의 모든 문장이 원본 컨텍스트에 근거하는지 확인	
Input : 생성된 답변(Answer), 참조 문서(Context), 사용자 질문(Query)	
Output : 환각 점수(Score) 및 통과 여부

함수 : check_answer_relevance(answer, query)	
설명 : 질문의 의도에 적합한 답변인지 평가	
Input : 답변(Answer), 사용자 질문(Query)	
Output : 관련성 평가 점수

"""