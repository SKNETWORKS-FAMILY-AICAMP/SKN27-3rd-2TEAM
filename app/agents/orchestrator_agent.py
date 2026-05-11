import logging
import time
from uuid import uuid4

from app.agents.input_planner_agent import InputPlannerAgent
from app.agents.intent_agent import IntentAgent
from app.agents.kag_dispatch_agent import KagDispatchAgent
from app.agents.rag_dispatch_agent import RagDispatchAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.response_generator import ResponseGenerator
from app.common.default_state import FALLBACK_RESPONSE_STATE
from app.validators.contract_validator import ContractValidator
from app.validators.provenance_validator import ProvenanceValidator
from app.validators.response_validator import ResponseValidator

logger = logging.getLogger("rimas.agent.orchestrator")


class OrchestratorAgent:
    """전체 Agent 흐름을 제어한다.

    Chatbot 흐름:
      InputPlanner → KagDispatch → ContractValidator → RagDispatch
        → IntentAgent → RecommendationAgent → ResponseGenerator
          → ResponseValidator → ProvenanceValidator

    Main Recommendation 흐름 (run_recommendation_only=True):
      InputPlanner → KagDispatch → ContractValidator → RagDispatch → view model 반환
    """

    def __init__(
        self,
        input_planner: InputPlannerAgent | None = None,
        kag_agent: KagDispatchAgent | None = None,
        rag_agent: RagDispatchAgent | None = None,
        intent_agent: IntentAgent | None = None,
        recommendation_agent: RecommendationAgent | None = None,
        response_generator: ResponseGenerator | None = None,
        contract_validator: ContractValidator | None = None,
        response_validator: ResponseValidator | None = None,
        provenance_validator: ProvenanceValidator | None = None,
    ):
        self._input_planner = input_planner or self._build_input_planner()
        self._kag = kag_agent or KagDispatchAgent()
        self._rag = rag_agent or RagDispatchAgent()
        self._intent = intent_agent or IntentAgent()
        self._rec = recommendation_agent or RecommendationAgent()
        self._gen = response_generator or ResponseGenerator()
        self._contract = contract_validator or ContractValidator()
        self._resp_val = response_validator or ResponseValidator()
        self._prov_val = provenance_validator or ProvenanceValidator()

    def run_chatbot(
        self,
        user_id: str,
        session_id: str,
        user_input: str,
        session_context: dict,
    ) -> dict:
        total_start = time.perf_counter()
        request_id = self._new_request_id()

        # 1. Input Planner — 사용자 입력을 INTENT_STATE/KAG_INPUT_JSON으로 정규화한다.
        planned_input = self._input_planner.run(
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            user_input=user_input,
            session_context=session_context,
        )
        intent_state = planned_input["intent_state"]
        kag_input_json = planned_input["kag_input_json"]

        # 2. KAG — KAG_INPUT_JSON 기준으로 추천 방향을 결정한다.
        kag_state = self._kag.run(
            user_id,
            user_input,
            session_context,
            kag_input_json=kag_input_json,
        )
        if kag_state.get("status") == "error":
            return self._fallback("KAG_DISPATCH_FAILED", kag_state, {})

        # 3. Contract Validation: SESSION_CONTEXT와 KAG_STATE 계약을 검증한다.
        contract_result = self._contract.validate(session_context, kag_state, {})
        if not contract_result["passed"]:
            logger.warning("contract_validation_failed", extra={"errors": contract_result["errors"]})
            return self._fallback("CONTRACT_VALIDATION_FAILED", kag_state, {})

        # 4. RAG — 추천 근거 검색
        rag_state = self._rag.run(
            kag_state,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            intent_state=intent_state,
            kag_input_json=kag_input_json,
        )
        if rag_state.get("status") == "error":
            return self._fallback("RAG_DISPATCH_FAILED", kag_state, rag_state)

        # 5. Intent Agent — Input Planner 결과를 검증/확정한다.
        intent_result = self._intent.run(
            user_input=user_input,
            kag_state=kag_state,
            rag_state=rag_state,
            intent_state=intent_state,
        )

        # 6. Recommendation Agent
        selected = self._rec.run(intent_result=intent_result, rag_state=rag_state)
        if not selected.get("selected_recommendations"):
            return self._fallback("NO_RECOMMENDATIONS", kag_state, rag_state)

        # 7. Response Generator
        try:
            response_state = self._gen.run(
                user_input=user_input,
                session_context=session_context,
                kag_state=kag_state,
                rag_state=rag_state,
                intent_result=intent_result,
                selected_recommendations=selected,
            )
        except Exception as exc:
            logger.error("response_generator_error", extra={"error": str(exc)}, exc_info=True)
            return self._fallback("LLM_CALL_FAILED", kag_state, rag_state)

        # 8. Validation
        resp_result = self._resp_val.validate(response_state)
        prov_result = self._prov_val.validate(response_state, rag_state)
        if not resp_result["passed"] or not prov_result["passed"]:
            errors = resp_result.get("errors", []) + prov_result.get("errors", [])
            logger.warning("response_validation_failed", extra={"errors": errors})
            return self._fallback("RESPONSE_VALIDATION_FAILED", kag_state, rag_state)

        ms = round((time.perf_counter() - total_start) * 1000, 1)
        logger.info("orchestrator_chatbot_ok", extra={"user_id": user_id, "ms": ms})

        return {
            **response_state,
            "_meta": {
                "kag_state": kag_state,
                "rag_state": rag_state,
                "latency_ms": ms,
            },
        }

    def run_recommendation(
        self,
        user_id: str,
        session_id: str,
        session_context: dict,
    ) -> dict:
        """메인 추천 페이지용 — LLM 없이 KAG+RAG만 실행한다."""
        total_start = time.perf_counter()
        request_id = self._new_request_id()

        planned_input = self._input_planner.run(
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            user_input="",
            session_context=session_context,
        )

        kag_state = self._kag.run(
            user_id,
            "",
            session_context,
            kag_input_json=planned_input["kag_input_json"],
        )
        if kag_state.get("status") == "error":
            return {"status": "error", "kag_state": kag_state, "rag_state": {}}

        rag_state = self._rag.run(
            kag_state,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            intent_state=planned_input["intent_state"],
            kag_input_json=planned_input["kag_input_json"],
        )

        ms = round((time.perf_counter() - total_start) * 1000, 1)
        logger.info("orchestrator_recommendation_ok", extra={"user_id": user_id, "ms": ms})

        return {
            "status": "success",
            "kag_state": kag_state,
            "rag_state": rag_state,
            "latency_ms": ms,
        }

    @staticmethod
    def _build_input_planner() -> InputPlannerAgent:
        try:
            from app.llm.openai_llm_client import MissingOpenAiApiKeyError, OpenAiLlmClient
            llm_client = OpenAiLlmClient()
            logger.info("input_planner_llm_enabled")
            return InputPlannerAgent(llm_client=llm_client)
        except Exception as exc:
            logger.info("input_planner_rule_based_fallback", extra={"reason": str(exc)})
            return InputPlannerAgent()

    @staticmethod
    def _new_request_id() -> str:
        return f"req_{uuid4().hex}"

    @staticmethod
    def _fallback(error_type: str, kag_state: dict, rag_state: dict) -> dict:
        logger.warning("orchestrator_fallback", extra={"error_type": error_type})
        return {
            **dict(FALLBACK_RESPONSE_STATE),
            "_meta": {
                "kag_state": kag_state,
                "rag_state": rag_state,
                "error_type": error_type,
                "latency_ms": 0,
            },
        }
