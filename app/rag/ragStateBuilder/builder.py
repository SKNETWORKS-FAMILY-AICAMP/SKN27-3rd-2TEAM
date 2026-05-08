"""
# 전체 시스템 조립
- 앞선 구성 요소들을 결합하여 실행 가능한 워크플로우 객체(CompiledGraph)를 생성합니다.

함수 : build_rag_graph()	
설명 : StateGraph를 초기화하고 노드와 엣지를 연결	
Input : nodes, edges, schema 구성 요소	
Output : StateGraph 객체

함수 : compile_graph(graph)	
설명 : 조립된 그래프를 실행 가능한 형태로 컴파일	
Input : StateGraph 객체	
Output : CompiledGraph (invoke() 실행 가능한 상태 머신)
"""