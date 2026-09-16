"""Creating providers for which an API key is available."""

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from lab.providers.base import Provider

# Environment variables each SDK reads, in the order the SDK prefers them.
API_KEY_VARIABLES: dict[str, tuple[str, ...]] = {
    "openai": ("OPENAI_API_KEY",),
    "anthropic": ("ANTHROPIC_API_KEY",),
    "google": ("GOOGLE_API_KEY", "GEMINI_API_KEY"),
    "mock": (),
}


@dataclass(frozen=True)
class AvailableProviders:
    providers: Mapping[str, Provider]
    missing_keys: Mapping[str, tuple[str, ...]]


def has_api_key(name: str, environ: Mapping[str, str]) -> bool:
    variables = API_KEY_VARIABLES[name]
    return not variables or any(environ.get(variable) for variable in variables)


def create_provider(name: str) -> Provider:
    # Imported lazily, so a reader with one key never needs the other SDKs configured.
    if name == "openai":
        from lab.providers.openai_provider import OpenAIProvider

        return OpenAIProvider()
    if name == "anthropic":
        from lab.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider()
    if name == "google":
        from lab.providers.google_provider import GoogleProvider

        return GoogleProvider()
    if name == "mock":
        from lab.providers.mock import MockProvider

        return MockProvider()
    raise ValueError(f"Unknown provider: {name}")


def available_providers(
    names: Iterable[str], environ: Mapping[str, str] | None = None
) -> AvailableProviders:
    env = os.environ if environ is None else environ
    wanted = sorted(set(names))
    return AvailableProviders(
        providers={name: create_provider(name) for name in wanted if has_api_key(name, env)},
        missing_keys={
            name: API_KEY_VARIABLES[name] for name in wanted if not has_api_key(name, env)
        },
    )
