"""Season 5: multi-turn messages, tool definitions, tool calls and image inputs.

These are the neutral shapes each adapter maps to its provider. They live apart from `base.py`
so the single-prompt request used by Seasons 1 to 4 stays as it was.
"""

import base64
import hashlib
import json
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Role = Literal["user", "assistant", "tool"]
ToolChoice = Literal["auto", "required", "none"]
ImageMediaType = Literal["image/png", "image/jpeg", "image/webp"]
ImageDetail = Literal["low", "high", "auto"]

# Provider tool names: letters, digits, underscores and hyphens, at most 64 characters.
_TOOL_NAME_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"


class ImagePart(BaseModel):
    """An image held by reference: the request carries its hash, not its bytes.

    Keeping bytes out of the request keeps cache entries small. The request hash covers the
    image's content (sha256) and not where the file sits, so a moved file still hits the cache.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    media_type: ImageMediaType
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    path: str = Field(min_length=1)
    # OpenAI only; the other adapters ignore it.
    detail: ImageDetail = "auto"

    @classmethod
    def from_file(cls, path: Path, *, detail: ImageDetail = "auto") -> Self:
        data = path.read_bytes()
        return cls(
            media_type=_media_type_for(path),
            sha256=hashlib.sha256(data).hexdigest(),
            path=path.as_posix(),
            detail=detail,
        )

    def read_bytes(self) -> bytes:
        """The image's bytes, refused if the file no longer matches the hash in the request."""
        data = Path(self.path).read_bytes()
        if hashlib.sha256(data).hexdigest() != self.sha256:
            raise ValueError(f"image {self.path} does not match its recorded sha256")
        return data

    def base64(self) -> str:
        return base64.b64encode(self.read_bytes()).decode("ascii")


def _media_type_for(path: Path) -> ImageMediaType:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix in (".jpg", ".jpeg"):
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    raise ValueError(f"unsupported image type: {path.name}")


class ToolSpec(BaseModel):
    """A tool the model may call: its name, when to use it, and a JSON schema for arguments."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(pattern=_TOOL_NAME_PATTERN)
    description: str
    parameters: dict[str, Any]
    # Ask the provider to hold arguments to the schema exactly, where it can (E3's strict arm).
    strict: bool = False


class ToolCall(BaseModel):
    """One tool call the model asked for.

    Arguments are kept as the raw JSON text the model wrote, so malformed arguments can be
    counted (E2, E3) rather than lost in parsing.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    call_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    arguments_json: str
    # Gemini 3 returns a thought signature with each call that must be sent back unchanged.
    signature: str | None = None

    def arguments(self) -> dict[str, Any]:
        """Parsed arguments. Raises ValueError if the model wrote invalid JSON or not an object."""
        try:
            value = json.loads(self.arguments_json or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError(f"arguments are not valid JSON: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise ValueError("arguments are not a JSON object")
        return value


class Message(BaseModel):
    """One turn: a user turn (text and images), an assistant turn (text and tool calls), or a
    tool result answering one call."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: Role
    text: str = ""
    images: tuple[ImagePart, ...] = ()
    tool_calls: tuple[ToolCall, ...] = ()
    # Tool results only: which call this answers, the tool's name (Gemini needs it) and whether
    # the tool reported an error.
    tool_call_id: str | None = None
    tool_name: str | None = None
    is_error: bool = False

    @model_validator(mode="after")
    def _fields_match_role(self) -> Self:
        if self.images and self.role != "user":
            raise ValueError("only user turns carry images")
        if self.tool_calls and self.role != "assistant":
            raise ValueError("only assistant turns carry tool calls")
        is_tool = self.role == "tool"
        if is_tool != (self.tool_call_id is not None and self.tool_name is not None):
            raise ValueError(
                "a tool result needs tool_call_id and tool_name; other turns have none"
            )
        if self.is_error and not is_tool:
            raise ValueError("only tool results can be errors")
        return self


def user(text: str, images: tuple[ImagePart, ...] = ()) -> Message:
    return Message(role="user", text=text, images=images)


def tool_result(call: ToolCall, content: str, *, is_error: bool = False) -> Message:
    return Message(
        role="tool",
        text=content,
        tool_call_id=call.call_id,
        tool_name=call.name,
        is_error=is_error,
    )


def hash_payload(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Messages as hashed: image paths are dropped so only image content counts."""
    return [
        {**message, "images": [_without_path(image) for image in message.get("images", [])]}
        for message in messages
    ]


def _without_path(image: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in image.items() if key != "path"}
