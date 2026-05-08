# 흐름 확인

rimas/
  app/
    main.py

common/
  constants.py
  default_state.py
  labels.py

pages/
  main_recommendation_page.py
  chatbot_page.py

ui/
  components/
    sidebar.py
    top_taste_header.py
    character_dj_banner.py
    personalized_recommendation_section.py
    new_release_section.py
    discovery_section.py
    recommendation_card_section.py
    personalized_guide_section.py
    music_taste_section.py
    chat_area.py
    chatbot_header.py
    related_recommendation_cards.py
    developer_debug_panel.py

  styles/
    theme.py
    css.py

services/
  main_recommendation_service.py
  chatbot_service.py
  llm_flow_service.py
  validation_service.py
  logging_service.py
  view_model_service.py

agents/
  intent_agent.py
  curation_agent.py
  recommendation_agent.py
  response_generator.py

adapters/
  kag_adapter.py
  rag_adapter.py
  mock_kag_adapter.py
  mock_rag_adapter.py
  real_kag_adapter.py
  real_rag_adapter.py

validators/
  contract_validator.py
  response_validator.py
  provenance_validator.py

repositories/
  ml_output_repository.py
  interaction_log_repository.py
  query_constants.py

schemas/
  ml_output_schema.py
  kag_state_schema.py
  rag_state_schema.py
  intent_result_schema.py
  curation_plan_schema.py
  selected_recommendation_schema.py
  response_state_schema.py
  interaction_log_schema.py

contracts/
  fields.py
  enums.py

json_templates/
  ml_output_template.json
  kag_state_template.json
  rag_state_template.json
  intent_result_template.json
  curation_plan_template.json
  selected_recommendations_template.json
  response_state_template.json
  interaction_log_template.json

config/
  settings.py

  docs/
    Design.md
    기능정의서.md
    요구사항 정의서.md
    WBS.md
    JSON_CONTRACT.md
    UX_IMPLEMENTATION_PLAN.md

  tests/
    test_contract_validator.py
    test_response_validator.py
    test_provenance_validator.py
    test_main_recommendation_service.py
    test_chatbot_service.py
    test_mock_kag_adapter.py
    test_mock_rag_adapter.py