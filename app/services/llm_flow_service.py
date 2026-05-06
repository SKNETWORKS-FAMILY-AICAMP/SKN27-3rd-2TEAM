from app.agents.curation_agent import CurationAgent
from app.agents.intent_agent import IntentAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.response_generator import ResponseGenerator
from app.common.default_state import FALLBACK_RESPONSE_STATE


class LlmFlowService:
    def __init__(
        self,
        intent_agent=None,
        curation_agent=None,
        recommendation_agent=None,
        response_generator=None,
    ):
        self._intent_agent = intent_agent or IntentAgent()
        self._curation_agent = curation_agent or CurationAgent()
        self._recommendation_agent = recommendation_agent or RecommendationAgent()
        self._response_generator = response_generator or ResponseGenerator()

    def run(self, user_input, ml_output, kag_state, rag_state):
        intent_result = self._intent_agent.run(
            user_input=user_input,
            kag_state=kag_state,
            rag_state=rag_state,
        )
        curation_plan = self._curation_agent.run(
            intent_result=intent_result,
            kag_state=kag_state,
            rag_state=rag_state,
        )
        selected_recommendations = self._recommendation_agent.run(
            curation_plan=curation_plan,
            rag_state=rag_state,
        )
        if not selected_recommendations.get("selected_recommendations"):
            return dict(FALLBACK_RESPONSE_STATE)

        return self._response_generator.run(
            user_input=user_input,
            ml_output=ml_output,
            kag_state=kag_state,
            rag_state=rag_state,
            curation_plan=curation_plan,
            selected_recommendations=selected_recommendations,
        )
