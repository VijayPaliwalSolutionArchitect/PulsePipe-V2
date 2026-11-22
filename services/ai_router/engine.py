from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from services.common.db import db


@dataclass
class ModelSpec:
    id: str
    pool: str
    display_name: str
    cost_per_1k_input_usd: float
    cost_per_1k_output_usd: float
    monthly_budget_usd: float


DEFAULT_MODELS: Dict[str, ModelSpec] = {
    "groq/llama-3.3-70b": ModelSpec("groq/llama-3.3-70b", "ultra-fast", "Llama 3.3 70B (Fast Reply Classifier)", 0.00059, 0.00079, 60.0),
    "openai/gpt-4o-mini": ModelSpec("openai/gpt-4o-mini", "balanced", "GPT-4o Mini (SDR Personalizer)", 0.00015, 0.00060, 120.0),
    "anthropic/claude-3-5-sonnet": ModelSpec("anthropic/claude-3-5-sonnet", "high-reasoning", "Claude 3.5 Sonnet (Objection Handler)", 0.00300, 0.01500, 250.0),
    "google/gemini-2.0-flash": ModelSpec("google/gemini-2.0-flash", "economy", "Gemini 2.0 Flash (Bulk Sequences)", 0.00010, 0.00040, 50.0),
    "local/qwen2.5": ModelSpec("local/qwen2.5", "offline", "Qwen 2.5 14B (Local Privacy Mode)", 0.0, 0.0, 0.0)
}

DEFAULT_POOLS: Dict[str, List[str]] = {
    "ultra-fast": ["groq/llama-3.3-70b"],
    "balanced": ["openai/gpt-4o-mini"],
    "high-reasoning": ["anthropic/claude-3-5-sonnet"],
    "economy": ["google/gemini-2.0-flash"],
    "offline": ["local/qwen2.5"]
}


class ModelSpendLedger:
    def __init__(self):
        self.spend_usd: Dict[str, float] = {m: 0.0 for m in DEFAULT_MODELS}
        self.call_count: Dict[str, int] = {m: 0 for m in DEFAULT_MODELS}

    def record_usage(self, model_id: str, cost: float):
        if model_id in self.spend_usd:
            self.spend_usd[model_id] += cost
            self.call_count[model_id] += 1

    def get_summary(self) -> Dict[str, Any]:
        return {
            "spend_usd": {k: round(v, 6) for k, v in self.spend_usd.items()},
            "call_count": self.call_count
        }


class FivePoolBudgetRouter:
    def __init__(self):
        self.registry = DEFAULT_MODELS.copy()
        self.pools = DEFAULT_POOLS.copy()
        self.ledger = ModelSpendLedger()

    def resolve_model(self, tenant_id: str, requested_pool: str = "balanced") -> ModelSpec:
        tenant = db.get_tenant(tenant_id)
        if tenant and tenant["current_spend_usd"] >= tenant["hard_cap_usd"]:
            return self.registry["local/qwen2.5"]

        candidates = self.pools.get(requested_pool, self.pools["balanced"])
        spec = self.registry.get(candidates[0], self.registry["openai/gpt-4o-mini"])

        if spec.monthly_budget_usd > 0 and self.ledger.spend_usd.get(spec.id, 0.0) >= spec.monthly_budget_usd:
            return self.registry["local/qwen2.5"]

        return spec

    def execute_call(self, tenant_id: str, pool: str, prompt: str) -> Dict[str, Any]:
        t0 = time.time()
        spec = self.resolve_model(tenant_id, pool)

        tokens_in = len(prompt.split()) * 2
        tokens_out = 120
        cost = (tokens_in / 1000.0) * spec.cost_per_1k_input_usd + (tokens_out / 1000.0) * spec.cost_per_1k_output_usd

        self.ledger.record_usage(spec.id, cost)
        db.update_tenant_spend(tenant_id, cost)
        duration_ms = round((time.time() - t0) * 1000.0 + 28.0, 2)

        return {
            "model_id": spec.id,
            "pool": spec.pool,
            "cost_usd": round(cost, 6),
            "tokens_used": tokens_in + tokens_out,
            "latency_ms": duration_ms
        }


global_router = FivePoolBudgetRouter()
