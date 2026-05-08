구분,전략명,주요 특징
추천 구조,Hybrid Retrieval,"1차로 필터를 통해 후보군을 좁히고, 2차로 의미적 순위 재조정(Reranking)을 수행하여 정확도를 높입니다."
검색 엔진,Hybrid Search,Elasticsearch를 활용하여 메타데이터 필터와 벡터 유사도 검색을 동시에 실행합니다.
리트리버,Multi-stage,필터링 → 유사도 검색 → 리랭킹의 3단계 구조로 프로덕션 품질을 확보합니다.


2. 🧠 데이터 및 임베딩 설계 (Data & Embedding)
AI가 데이터를 더 잘 이해하고 관리할 수 있도록 구조화합니다.

🧩 하이브리드 청킹 (Hybrid Chunking)
Track + Playlist Context: 곡 단위의 정보와 플레이리스트의 전체 맥락을 함께 묶어서 저장합니다.

효과: 추천의 질을 높이는 것은 물론, 사용자에게 설명할 풍부한 근거 자료가 됩니다.

🏷️ 임베딩 전략
Metadata + Description: 단순 텍스트뿐만 아니라 정해진 규격(메타데이터)을 함께 임베딩하여 시스템의 정합성을 유지합니다.


3. 🛠️ 인프라 및 운영 구조 (Infra & Ops)
중단 없는 서비스와 효율적인 디버깅을 위한 설계입니다.

🔄 하이브리드 에일리어스 (Hybrid Alias)
구조: track_v1, track_v2와 같은 실제 인덱스를 tracks_current라는 별칭(Alias)으로 연결합니다.

장점: 새로운 데이터 모델을 배포할 때 서비스 중단 없이 즉시 교체가 가능합니다.


📋 추천 사유 추적 수첩 (RAG_STATE)
시스템 내부에서 어떤 경로로 추천이 이루어졌는지 모든 흔적을 남깁니다.

{
  "retrieval_trace": {
    "retrieval_strategy": "Hybrid",
    "retrieval_filters": ["genre:Jazz", "year:>2020"],
    "matched_fields": ["mood", "instrumental"],
    "score_breakdown": [0.85, 0.12]
  }
}

4. 👑 시스템 지휘 체계 (Supervisor)
전체 워크플로우를 유연하게 관리합니다.

🕸️ 그래프 기반 워크플로우 (Graph-based Workflow)
LangGraph 스타일: 고정된 순서가 아니라, 상황에 따라 분기(Decision)하고 다시 돌아오는(Fallback) 유연한 흐름을 가집니다.

핵심 가치: 복잡한 상태 관리가 가능해지며, 특정 단계에서 오류가 발생해도 시스템이 유연하게 대처할 수 있습니다.

============================================================================


# RAG 전용 파일 구조 정의
## (Hybrid Retrieval + Multi-stage + Provenance 기반)

본 구조는 다음 설계를 기준으로 한다.

- Hybrid Retrieval
- Hybrid Search
- Multi-stage Retrieval
- Hybrid Chunking
- Hybrid Metadata + Embedding
- Retrieval Trace
- Provenance Validation
- Design.md 계약 구조 유지

---

# 1. RAG 최상위 구조

```text
app/
└── rag/
    ├── chunkers/ Hybrid Chunking 담당
            │
            ├── track_chunker.py
            ├── playlist_chunker.py
            ├── hybrid_chunker.py
            └── chunk_metadata_builder.py
    ├── embeddings/ Embedding 생성 담당
            │
            ├── embedding_service.py
            ├── metadata_embedding.py
            ├── description_embedding.py
            ├── hybrid_embedding_builder.py
            └── embedding_cache.py
    ├── indexing/ Elasticsearch Index 관리
            │
            ├── index_builder.py
            ├── elastic_mapping_builder.py
            ├── alias_manager.py
            ├── bulk_indexer.py
            └── reindex_pipeline.py
    ├── retrievers/ Multi-stage Retrieval 핵심
            │
            ├── metadata_retriever.py
            ├── vector_retriever.py
            ├── hybrid_retriever.py
            ├── multi_stage_retriever.py
            ├── retrieval_policy_builder.py
            └── retrieval_orchestrator.py
    ├── rerankers/ Semantic reranking 담당
            │
            ├── semantic_reranker.py
            ├── personalization_reranker.py
            ├── diversity_reranker.py
            └── rerank_pipeline.py
    ├── vectorstores/ Elasticsearch Query 계층
            │   
            ├── elasticsearch_store.py
            ├── metadata_filter_builder.py
            ├── vector_query_builder.py
            └── hybrid_query_builder.py
    ├── builders/ RAG_STATE 생성 담당
            │
            ├── rag_state_builder.py
            ├── recommendation_evidence_builder.py
            ├── recommendation_reason_builder.py
            ├── information_evidence_builder.py
            └── recommendation_script_builder.py
    ├── validators/ RAG 검증 계층
            │
            ├── retrieval_validator.py
            ├── rerank_validator.py
            ├── rag_contract_validator.py
            └── provenance_validator.py
    ├── tracing/ Retrieval Trace 관리
            │
            ├── retrieval_trace_builder.py
            ├── retrieval_trace_logger.py
            ├── score_trace_builder.py
            └── debug_trace_exporter.py
    ├── schemas/ RAG 전용 JSON 계약
            │
            ├── rag_state_schema.py
            ├── retrieval_trace_schema.py
            ├── retrieval_result_schema.py
            ├── rerank_result_schema.py
            ├── recommendation_evidence_schema.py
            └── information_evidence_schema.py
    ├── workflows/ Graph 기반 workflow
            │
            ├── retrieval_workflow.py
            ├── rerank_workflow.py
            ├── rag_generation_workflow.py
            └── fallback_workflow.py
    ├── repositories/ RAG 데이터 소스 접근
            │
            ├── music_catalog_repository.py
            ├── playlist_repository.py
            └── embedding_repository.py
    ├── constants/ RAG 전용 상수
            │
            ├── retrieval_constants.py
            ├── embedding_constants.py
            ├── rerank_constants.py
            └── index_constants.py



key - kag 

├── services/ RAG 실행 서비스 계층
        │
        ├── retrieval_service.py
        ├── indexing_service.py
        ├── embedding_service.py
        └── rag_generation_service.py

├── adapters/ RAG 외부 인터페이스 계층
        │
        ├── rag_adapter.py
        ├── mock_rag_adapter.py
        └── real_rag_adapter.py

folder - services (RAG 실행 서비스 계층)
이 계층은 개별 기술 단위의 로직을 수행하며, 주로 RagStateBuilder에서 호출되어 사용됩니다.
file - indexing_service.py (문서 인덱싱)
함수:
process_and_index(raw_data): 원본 문서를 청킹(Chunking)하고 메타데이터를 추출하여 저장 준비.
update_index(document_id, new_data): 기존 인덱싱된 데이터를 수정.
input: PDF, 텍스트 파일 등의 원본 데이터.
output: 인덱싱 완료 상태 및 문서 ID.

file - embedding_service.py (벡터 변환)
함수:
get_embeddings(text_list): 텍스트를 고차원 벡터로 변환.
calculate_similarity(vec1, vec2): 벡터 간의 유사도 계산.
input: 텍스트 리스트 또는 쿼리.
output: 벡터 데이터(List[float]).

file - retrieval_service.py (지식 검색)
함수:
retrieve_relevant_docs(query, k): 쿼리와 가장 유사한 k개의 문서 조각을 검색.
rerank_documents(query, docs): 검색된 결과의 순위를 재정렬하여 정확도 향상.
input: 사용자 질문(Query), 검색 개수(k).
output: 검색된 관련 문서 리스트.

file - rag_generation_service.py (답변 생성 서비스)
함수:
construct_prompt(context, question): 검색된 지식과 질문을 결합하여 최적의 프롬프트 구성.
invoke_llm(prompt): LLM을 호출하여 최종 답변 생성.
input: 검색 결과(Context), 질문.
output: 생성된 최종 텍스트 답변.

============================================================================

folder - adapters (RAG 외부 인터페이스 계층)
이 계층은 외부 라이브러리(LangChain, LlamaIndex 등)나 API와의 의존성을 분리하는 '완충 지대' 역할을 합니다.
file - rag_adapter.py (추상 인터페이스)
함수:
run_workflow(input_data): RAG 워크플로우를 실행하는 추상 메서드.
input: 사용자 입력 객체.
output: 최종 응답 객체.

file - real_rag_adapter.py (실제 구현체)
함수:
connect_langgraph(builder): 실제 LangGraph나 외부 엔진에 연결하여 그래프 실행.
handle_external_api(payload): OpenAI나 Anthropic API 등 외부 인프라와의 통신 처리.
input: 서비스 계층에서 가공된 데이터.
output: 외부 엔진으로부터 받은 가공되지 않은(Raw) 응답 데이터.

file - mock_rag_adapter.py (테스트용 모의 객체)
함수:
get_dummy_response(query): 실제 API 호출 없이 테스트용 가짜 답변 반환.
input: 테스트용 쿼리.
output: 미리 정의된 더미 답변 데이터.

============================================================================

folder - MusicCatalogRepository (데이터 접근)
file - base_repository.py (추상 인터페이스)
- 함수
get_by_id(id): ID로 조회
search_by_metadata(filters): 필터 조건으로 조회
list_all(): 목록 조회
- input
- output
file - sql_repository.py (실제 구현체)
- 함수
엘라스틱서치의 데이터 가져오기
SQLAlchemy나 Django ORM 등을 사용하여 실제 DB 세션 처리.
Music 테이블과 Contract 테이블을 Join하여 데이터를 가져오는 구체적인 로직.
- input
- output
============================================================================
folder - RagStateBuilder (상태 조립)
file - schema.py (데이터 규격 정의)
이 파일은 전체 그래프 흐름에서 유지되고 전달될 데이터의 '청사진'을 정의합니다.
함수 (Class 정의):
RagState(TypedDict): 전체 워크플로우에서 공유될 상태 변수들의 집합.
input: 질문(String), 채팅 이력(List) 등 사용자의 초기 입력.
output: 검색된 문서 리스트(List[Document]), 생성된 답변(String), 재검색 필요 여부(Boolean) 등.

file - nodes.py (구체적인 처리 로직)
상태를 입력받아 특정 작업을 수행하고 상태를 업데이트하는 개별 작업 단위입니다.
함수:
retrieve_documents(state): 질문에 관련된 지식을 벡터 DB에서 검색.
generate_answer(state): 검색된 컨텍스트와 질문을 바탕으로 LLM을 통해 답변 생성.
grade_documents(state): 검색된 문서들이 질문과 관련이 있는지 평가 및 필터링.
transform_query(state): 검색 결과가 부실할 경우 질문을 더 나은 형태로 재작성.
input: RagState (현재까지의 상태)
output: RagState (해당 노드의 작업 결과가 업데이트된 상태)

file - edges.py (경로 및 조건 설정)
흐름의 갈림길에서 다음에 어떤 노드로 이동할지 결정하는 조건부 로직을 담당합니다.
함수:
decide_to_generate(state): grade_documents 결과에 따라 '답변 생성'으로 갈지 '질문 재작성'으로 갈지 결정.
check_hallucination(state): 생성된 답변이 문서 내용에 기반하는지 판단하여 최종 완료 여부 결정.
input: RagState (평가 결과가 담긴 상태)
output: 다음으로 실행할 '노드의 이름' (String)

file - builder.py (전체 시스템 조립)
앞선 구성 요소들을 결합하여 실행 가능한 워크플로우 객체(Graph)를 생성합니다.
함수:
build_rag_graph(): StateGraph를 초기화하고 노드와 엣지를 연결.
compile_graph(graph): 조립된 그래프를 실행 가능한 바이너리/객체 형태로 컴파일.
input: 각 파일(nodes, edges, schema)에서 정의된 함수와 클래스들.
output: CompiledGraph (실제 invoke()를 호출하여 실행할 수 있는 상태 머신)
============================================================================
folder - ContractValidator (검증 로직)
file - base_validator.py (추상 인터페이스)
모든 검증기들이 공통적으로 가져야 할 규격을 정의합니다.
함수:
validate(data): 입력 데이터의 유효성을 검사하는 기본 추상 메서드.
get_error_report(): 검증 실패 시 상세 사유를 반환하는 메서드.
input: 검증 대상 데이터 (계약서 텍스트, 메타데이터 등).
output: 검증 결과 (Boolean) 및 에러 메시지.

file - format_validator.py (형식 및 스키마 검증)
데이터가 시스템이 이해할 수 있는 올바른 형식(JSON, PDF 구조 등)인지 확인합니다.
함수:
check_required_fields(contract_data): 필수 계약 항목(당사자, 일자, 금액 등)의 누락 여부 확인.
validate_data_types(contract_data): 날짜 형식이나 숫자 단위가 올바른지 확인.
input: 추출된 계약 데이터 객체.
output: 형식 일치 여부 결과.

file - logic_validator.py (비즈니스 로직 및 정책 검증)
계약 내용이 법적/사업적 정책이나 기존 데이터와 모순되지 않는지 확인합니다.
함수:
verify_contract_period(start_date, end_date): 시작일이 종료일보다 앞서는지 등 기간 논리 확인.
cross_check_with_db(contract_info): 기존에 등록된 계약과 중복되거나 충돌하는 조건이 있는지 DB 연동 확인.
check_compliance_rules(text): 특정 필수 문구나 금지 조항이 포함되었는지 검사.
input: 계약 상세 정보 및 DB 조회 데이터.
output: 로직 타당성 결과 및 위반 내역 리포트.

file - hallucination_validator.py (RAG 전용 환각 검증)
RAG 시스템에서 생성된 답변이 원본 계약서 내용에 충실한지(Faithfulness)를 검증합니다.
함수:
verify_grounding(answer, context): 생성된 답변의 모든 문장이 원본 컨텍스트에 근거하는지 확인.
check_answer_relevance(answer, query): 질문의 의도에 적합한 답변인지 평가.
input: 생성된 답변(Answer), 참조 문서(Context), 사용자 질문(Query).
output: 환각 점수(Score) 및 통과 여부.
============================================================================

최소 임베딩화 : 감정, 타이틀, 아티스트, 리딩(가사)

KAG_STATE가 언제 RAG로 들어가는지
RAG가 DB / Vector DB / Embedding / Reranker 중 어디까지 호출하는지
RAG_STATE가 언제 생성되는지
Validator가 RAG 앞에 있는지 뒤에 있는지
Service Layer가 RAG 내부 구현을 몰라도 되는지
LLM이 RAG를 직접 호출하지 않는지
전체 RAG 설계 자체는 필요합니다.
그래야 RAG가 KAG, DB, Service, LLM, Validator와 어디서 연결되는지 확인할 수 있고,
나중에 Real RAG로 확장할 때 구조 충돌을 미리 잡을 수 있습니다.
다만 문서 안에서 반드시 “전체 설계”와 “현재 구현 범위”를 분리해야 합니다.

전체 설계에는 다음을 포함해도 됩니다.
Hybrid Retrieval
Hybrid Search
Multi-stage Retrieval
Embedding
Elasticsearch
Reranking
Retrieval Trace
Provenance 기준
Index Alias/Reindex 전략

하지만 현재 MVP 구현 범위는 다음으로 제한하는 게 맞습니다.
MockRagAdapter
MusicCatalogRepository
RagStateBuilder
RagState Schema
Contract Validation
Provenance Validation

정리하면,
“RAG 전체 설계는 유지하되, 구현 우선순위는 MVP와 Real RAG 확장 단계로 분리하자”
가 맞습니다.
위에 말한 것과 같이 전반적인 전체 흐름은 잡는게 맞는데 구현 우선순위를 두는게 좋을 것같아요 확인해주세요 
그리고 RAG 전체 설계 기준으로 시퀀스 다이어그램을 만들어주세요! 
근데 그냥 전체가 아니라 지금 구현할 MVP 흐름이랑 나중에 확장할 Real RAG 흐름 으로 나눠서 작성 부탁드립니다
아래에 구분 기준 보내드릴게요
MVP RAG Flow
Service
MockRagAdapter
MusicCatalogRepository
RagStateBuilder
ContractValidator

Real RAG Flow
Service
RealRagAdapter
RetrievalOrchestrator
MetadataRetriever
VectorRetriever
Reranker
RagStateBuilder
RetrievalTraceBuilder
ContractValidator

중요 조건:
KAG_STATE는 RAG 입력으로만 사용
RAG는 KAG_STATE를 수정하지 않음
RAG는 최종 자연어 응답을 만들지 않음
RAG_STATE만 반환
LLM은 RAG 내부에서 호출하지 않음