"""Provider-specific model setup behind the workshop's LLM_* settings."""

import os


def provider_name() -> str:
    provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if provider not in {"openai", "anthropic"}:
        raise ValueError("Set LLM_PROVIDER to openai or anthropic.")
    return provider


def model_name() -> str:
    model = os.environ.get("LLM_MODEL", "").strip()
    if not model:
        raise ValueError("Set LLM_MODEL to a model supported by your LLM_PROVIDER.")
    return model


def credential_header(api_key: str) -> tuple[str, str]:
    if provider_name() == "anthropic":
        return "x-api-key", api_key
    return "Authorization", f"Bearer {api_key}"


def build_model(*, api_key: str, http_client=None):
    provider = provider_name()
    model = model_name()
    base_url = os.environ.get("LLM_BASE_URL", "").strip() or {
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com",
    }[provider]
    if provider == "openai":
        from pydantic_ai.models.openai import OpenAIResponsesModel
        from pydantic_ai.providers.openai import OpenAIProvider

        return OpenAIResponsesModel(model, provider=OpenAIProvider(
            api_key=api_key, base_url=base_url, http_client=http_client,
        ))

    import anthropic
    from pydantic_ai.models.anthropic import AnthropicModel
    from pydantic_ai.providers.anthropic import AnthropicProvider

    workspace = os.environ.get("LLM_WORKSPACE_ID", "").strip()
    client = anthropic.AsyncAnthropic(
        api_key=api_key, base_url=base_url, http_client=http_client,
        default_headers={"anthropic-workspace-id": workspace} if workspace else {},
    )
    return AnthropicModel(model, provider=AnthropicProvider(anthropic_client=client))
