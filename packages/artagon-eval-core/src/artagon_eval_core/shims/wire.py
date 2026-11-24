"""Frozen wire descriptors and compact JSON codecs for ADR-0012 hot-path shims."""

from __future__ import annotations

import importlib.util
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

HAVE_MSGSPEC: Final[bool] = importlib.util.find_spec("msgspec") is not None


def _empty_str_map() -> Mapping[str, str]:
    return MappingProxyType({})


def _as_str(data: Mapping[str, object], key: str) -> str:
    val = data.get(key)
    if not isinstance(val, str):
        msg = f"Expected string field {key!r}"
        raise TypeError(msg)
    return val


def _as_opt_str(data: Mapping[str, object], key: str) -> str | None:
    val = data.get(key)
    if val is None or isinstance(val, str):
        return val
    msg = f"Expected string or None for field {key!r}"
    raise ValueError(msg)


def _as_opt_int(data: Mapping[str, object], key: str) -> int | None:
    val = data.get(key)
    if val is None:
        return None
    if isinstance(val, int) and not isinstance(val, bool):
        return val
    msg = f"Expected int or None for field {key!r}"
    raise ValueError(msg)


def _as_str_tuple(data: Mapping[str, object], key: str) -> tuple[str, ...]:
    val = data.get(key)
    if val is None:
        return ()
    if isinstance(val, (list, tuple)) and all(isinstance(item, str) for item in val):
        return tuple(val)
    msg = f"Expected sequence of strings for field {key!r}"
    raise ValueError(msg)


def _as_str_map(data: Mapping[str, object], key: str) -> Mapping[str, str]:
    val = data.get(key)
    if val is None:
        return MappingProxyType({})
    if isinstance(val, Mapping):
        frozen: dict[str, str] = {}
        for k, v in val.items():
            if not isinstance(k, str) or not isinstance(v, str):
                msg = f"Expected string mapping for field {key!r}"
                raise TypeError(msg)
            frozen[k] = v
        return MappingProxyType(frozen)
    msg = f"Expected mapping for field {key!r}"
    raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class HotPathShimDescriptor:
    """Frozen hot-path shim descriptor with sensitive credential fields hidden from repr()."""

    schema_version: str
    trial_id: str
    campaign_id: str
    arm_id: str
    task_id: str
    harness: str
    auth_mode: str
    pin_mode: str
    execution_mode: str
    trial_root: str
    workspace_dir: str
    real_binary: str
    expected_binary_sha256: str
    shim_receipt_path: str
    child_execs_path: str
    hook_socket_path: str
    hook_fallback_path: str
    hook_hmac_key_hex: str = field(repr=False)
    model: str | None = None
    expected_binary_size: int | None = None
    expected_binary_mtime_ns: int | None = None
    secret_api_key_path: str | None = field(default=None, repr=False)
    secret_env_path: str | None = field(default=None, repr=False)
    api_key_env_name: str | None = None
    extra_argv: tuple[str, ...] = ()
    injected_env: Mapping[str, str] = field(default_factory=_empty_str_map)
    scrubbed_env_keys: tuple[str, ...] = ()
    otlp_endpoint: str | None = None
    otlp_bearer_token: str | None = field(default=None, repr=False)
    copilot_otel_file_path: str | None = None
    hook_stdout_acks: Mapping[str, str] = field(default_factory=_empty_str_map)

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> HotPathShimDescriptor:
        """Validate and construct a frozen descriptor from a parsed JSON mapping."""
        return cls(
            schema_version=_as_str(data, "schema_version"),
            trial_id=_as_str(data, "trial_id"),
            campaign_id=_as_str(data, "campaign_id"),
            arm_id=_as_str(data, "arm_id"),
            task_id=_as_str(data, "task_id"),
            harness=_as_str(data, "harness"),
            auth_mode=_as_str(data, "auth_mode"),
            pin_mode=_as_str(data, "pin_mode"),
            execution_mode=_as_str(data, "execution_mode"),
            trial_root=_as_str(data, "trial_root"),
            workspace_dir=_as_str(data, "workspace_dir"),
            real_binary=_as_str(data, "real_binary"),
            expected_binary_sha256=_as_str(data, "expected_binary_sha256"),
            shim_receipt_path=_as_str(data, "shim_receipt_path"),
            child_execs_path=_as_str(data, "child_execs_path"),
            hook_socket_path=_as_str(data, "hook_socket_path"),
            hook_fallback_path=_as_str(data, "hook_fallback_path"),
            hook_hmac_key_hex=_as_str(data, "hook_hmac_key_hex"),
            model=_as_opt_str(data, "model"),
            expected_binary_size=_as_opt_int(data, "expected_binary_size"),
            expected_binary_mtime_ns=_as_opt_int(data, "expected_binary_mtime_ns"),
            secret_api_key_path=_as_opt_str(data, "secret_api_key_path"),
            secret_env_path=_as_opt_str(data, "secret_env_path"),
            api_key_env_name=_as_opt_str(data, "api_key_env_name"),
            extra_argv=_as_str_tuple(data, "extra_argv"),
            injected_env=_as_str_map(data, "injected_env"),
            scrubbed_env_keys=_as_str_tuple(data, "scrubbed_env_keys"),
            otlp_endpoint=_as_opt_str(data, "otlp_endpoint"),
            otlp_bearer_token=_as_opt_str(data, "otlp_bearer_token"),
            copilot_otel_file_path=_as_opt_str(data, "copilot_otel_file_path"),
            hook_stdout_acks=_as_str_map(data, "hook_stdout_acks"),
        )


def encode_json_bytes(payload: Mapping[str, object], *, force_stdlib: bool = False) -> bytes:
    """Encode a JSON mapping to compact UTF-8 bytes with trailing newline."""
    if not force_stdlib and HAVE_MSGSPEC:
        import msgspec

        return msgspec.json.encode(dict(payload)) + b"\n"
    encoded = json.dumps(dict(payload), separators=(",", ":"), ensure_ascii=False)
    return (encoded + "\n").encode("utf-8")


def decode_descriptor_bytes(raw: bytes, *, force_stdlib: bool = False) -> HotPathShimDescriptor:
    """Decode UTF-8 JSON bytes into a frozen HotPathShimDescriptor."""
    parsed: object
    if not force_stdlib and HAVE_MSGSPEC:
        import msgspec

        parsed = msgspec.json.decode(raw, type=dict[str, object])
    else:
        parsed = json.loads(raw.decode("utf-8"))
    if not isinstance(parsed, Mapping):
        msg = "Descriptor JSON root must be an object"
        raise TypeError(msg)
    str_map: dict[str, object] = {}
    for k, v in parsed.items():
        if not isinstance(k, str):
            msg = "Descriptor JSON keys must be strings"
            raise TypeError(msg)
        str_map[k] = v
    return HotPathShimDescriptor.from_mapping(str_map)
