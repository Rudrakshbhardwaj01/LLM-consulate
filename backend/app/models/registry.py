from app.models.types import ModelDefinition

MODEL_REGISTRY: dict[str, ModelDefinition] = {
    "gpt-oss-120b": ModelDefinition(
        id="gpt-oss-120b",
        displayName="GPT-OSS 120B",
        provider="nvidia",
        provider_model_id="openai/gpt-oss-120b",
        role="Chief Analyst",
        description="Deep reasoning with structured synthesis and reasoning traces.",
        supportsReasoning=True,
        maxTokens=8192,
        temperature=0.6,
        topP=0.9,
        family="OpenAI",
        tags=["Reasoning", "Synthesis"],
    ),
    "minimax-m2.7": ModelDefinition(
        id="minimax-m2.7",
        displayName="MiniMax M2.7",
        provider="nvidia",
        provider_model_id="minimaxai/minimax-m2.7",
        role="Strategic Advisor",
        description="Long-form strategic reasoning with alternative viewpoints.",
        supportsReasoning=True,
        maxTokens=8192,
        temperature=0.7,
        topP=0.9,
        family="MiniMax",
        tags=["Strategic Reasoning"],
    ),
    "qwen3-next-80b": ModelDefinition(
        id="qwen3-next-80b",
        displayName="Qwen3 Next 80B",
        provider="nvidia",
        provider_model_id="qwen/qwen3-next-80b-a3b-instruct",
        role="Research Specialist",
        description="Research-heavy analysis with long-context reasoning.",
        supportsReasoning=True,
        maxTokens=8192,
        temperature=0.7,
        topP=0.9,
        family="Qwen",
        tags=["Research", "Long Context"],
    ),
    "nemotron-omni-30b": ModelDefinition(
        id="nemotron-omni-30b",
        displayName="Nemotron Omni 30B",
        provider="nvidia",
        provider_model_id="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        role="Independent Reviewer",
        description="Explicit reasoning with critical evaluation and challenge.",
        supportsReasoning=True,
        maxTokens=8192,
        temperature=0.5,
        topP=0.85,
        family="NVIDIA",
        tags=["Critical Review"],
    ),
    "kimi-k2.6": ModelDefinition(
        id="kimi-k2.6",
        displayName="Kimi K2.6",
        provider="nvidia",
        provider_model_id="moonshotai/kimi-k2.6",
        role="Creative Expert",
        description="Exploratory thinking with creative solutions and long-horizon planning.",
        supportsReasoning=False,
        maxTokens=8192,
        temperature=0.8,
        topP=0.95,
        family="Moonshot AI",
        tags=["Creative Thinking"],
    ),
    "gemma-3n-e2b": ModelDefinition(
        id="gemma-3n-e2b",
        displayName="Gemma 3N E2B",
        provider="nvidia",
        provider_model_id="google/gemma-3n-e2b-it",
        role="Conservative Analyst",
        description="Structured outputs with cautious, methodical recommendations.",
        supportsReasoning=False,
        maxTokens=4096,
        temperature=0.4,
        topP=0.85,
        family="Google",
        tags=["Structured Analysis"],
    ),
}

DEFAULT_SYNTHESIS_MODEL_ID = "gpt-oss-120b"
DEADLOCK_THRESHOLD = 0.60
MINORITY_DIVERGENCE_THRESHOLD = 0.45


def get_model(model_id: str) -> ModelDefinition | None:
    model = MODEL_REGISTRY.get(model_id)
    return model if model and model.enabled else None


def get_available_models() -> list[ModelDefinition]:
    return [m for m in MODEL_REGISTRY.values() if m.enabled]


def get_council_members() -> list[ModelDefinition]:
    return [m for m in get_available_models() if m.consulate_eligible]
