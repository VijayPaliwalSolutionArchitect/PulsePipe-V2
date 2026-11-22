from services.ai_router.engine import global_router

def test_model_resolution():
    spec = global_router.resolve_model(tenant_id="acme-sales", requested_pool="balanced")
    assert spec.id == "openai/gpt-4o-mini"

def test_hard_cap_fallback():
    spec = global_router.resolve_model(tenant_id="saas-growth", requested_pool="high-reasoning")
    assert spec.id in ("anthropic/claude-3-5-sonnet", "local/qwen2.5")
