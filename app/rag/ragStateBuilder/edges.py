"""
# 경로 및 조건 설정
- 흐름의 갈림길에서 다음에 어떤 노드로 이동할지 결정하는 조건부 로직을 담당합니다.

공통 Input	Output
Input : 생성 결과가 담긴 RagState	
Output : 다음 실행할 노드 이름 (String)

함수 : 	decide_to_generate(state)	
설명 : 	grade_documents 결과에 따라 답변 생성 또는 질문 재작성 방향 결정	

함수 : 	check_hallucination(state)	
설명 : 	생성된 답변이 문서 내용에 기반하는지 판단하여 최종 완료 여부 결정	

"""