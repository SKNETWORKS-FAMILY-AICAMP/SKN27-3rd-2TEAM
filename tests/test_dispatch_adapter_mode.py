from app.agents.kag_dispatch_agent import KagDispatchAgent
from app.agents.rag_dispatch_agent import RagDispatchAgent
from app.kag.adapters.mock_kag_adapter import MockKagAdapter
from app.kag.adapters.real_kag_adapter import RealKagAdapter
from app.rag.adapters.mock_rag_adapter import MockRagAdapter
from app.rag.adapters.rag_real_adapter import RealRagAdapter


def test_kag_dispatch_defaults_to_mock_adapter(monkeypatch):
    monkeypatch.delenv("RIMAS_KAG_MODE", raising=False)

    agent = KagDispatchAgent()

    assert isinstance(agent._adapter, MockKagAdapter)


def test_kag_dispatch_uses_real_adapter_when_env_mode_is_real(monkeypatch):
    monkeypatch.setenv("RIMAS_KAG_MODE", "real")

    agent = KagDispatchAgent()

    assert isinstance(agent._adapter, RealKagAdapter)


def test_rag_dispatch_defaults_to_mock_adapter(monkeypatch):
    monkeypatch.delenv("RIMAS_RAG_MODE", raising=False)

    agent = RagDispatchAgent()

    assert isinstance(agent._adapter, MockRagAdapter)


def test_rag_dispatch_uses_real_adapter_when_env_mode_is_real(monkeypatch):
    monkeypatch.setenv("RIMAS_RAG_MODE", "real")

    agent = RagDispatchAgent()

    assert isinstance(agent._adapter, RealRagAdapter)
