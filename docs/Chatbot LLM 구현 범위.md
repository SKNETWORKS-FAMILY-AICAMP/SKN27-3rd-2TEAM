# Chatbot LLM 구현 범위

이번 OpenAI LLM 구현 범위는 Chatbot Flow로 제한한다.

- OpenAI LLM 호출은 `ChatbotService -> LlmFlowService -> Response Generator` 흐름에서만 사용한다.
- Main Recommendation Page는 계속 LLM 없이 동작해야 한다.
- KAG/RAG 구현체 내부에서 LLM을 사용할 가능성은 배제하지 않는다.
- 다만 KAG/RAG 판단용 LLM은 별도 입출력 계약, 검증 기준, 실패 처리, provenance 기준이 필요하므로 이번 구현 범위에는 포함하지 않는다.
- KAG/RAG 내부 LLM을 추가하려면 `RealKagAdapter`, `RealRagAdapter`의 계약 문서를 먼저 확정한 뒤 구현한다.
