"""Closed EvalError ADT, NormativeExitCode mapping, and unified CLI Envelope[T]."""

from __future__ import annotations

from enum import IntEnum
from typing import Annotated, Literal, assert_never

from expression import Error, Ok, Result
from pydantic import Field, ValidationError

from artagon_eval_core.domain.primitives import (
    ConfinedScratchPath,
    NonEmptyStr,
    RedactedJsonValue,
    RedactedStr,
    RelativeRepoPath,
    SafeId,
    static_redacted_literal,
)
from artagon_eval_core.domain.types import (
    FrozenModel,
    PersistentMap,
    empty_persistent_map,
)


class NormativeExitCode(IntEnum):
    """Single canonical exit-code contract shared by harness-eval, skill-eval, and all adapters."""

    OK = 0
    GATE_REJECTED = 1
    SCHEMA_USAGE = 2
    CREDENTIAL_UNAVAILABLE = 3
    BILLING_GUARD = 4
    ISOLATION_TAMPER = 5
    VERIFIER_CASSETTE = 6
    QUOTA_CENSORED = 7
    MULTIPLEXER = 8
    CLI_USAGE = 64
    DATA_SPLIT_ERROR = 65
    ADAPTER_UNAVAILABLE = 69


FailureExitCode = Literal[
    NormativeExitCode.GATE_REJECTED,
    NormativeExitCode.SCHEMA_USAGE,
    NormativeExitCode.CREDENTIAL_UNAVAILABLE,
    NormativeExitCode.BILLING_GUARD,
    NormativeExitCode.ISOLATION_TAMPER,
    NormativeExitCode.VERIFIER_CASSETTE,
    NormativeExitCode.QUOTA_CENSORED,
    NormativeExitCode.MULTIPLEXER,
    NormativeExitCode.CLI_USAGE,
    NormativeExitCode.DATA_SPLIT_ERROR,
    NormativeExitCode.ADAPTER_UNAVAILABLE,
]

MutationScope = Literal[
    "none",
    "frozen_manifest",
    "campaign_artifacts",
    "candidate_bundle",
    "promotion_patch",
    "state_ledger",
]


class _BaseEvalError(FrozenModel):
    """Deeply frozen structured error; raw unredacted str cannot construct message or details."""

    reason_code: NonEmptyStr
    message: RedactedStr
    details: PersistentMap[str, RedactedJsonValue] = Field(default_factory=empty_persistent_map)
    log_paths: tuple[RelativeRepoPath | ConfinedScratchPath, ...] = ()
    redacted: Literal[True] = True


class GateRejectedError(_BaseEvalError):
    kind: Literal["gate_rejected"] = "gate_rejected"
    exit_code: Literal[NormativeExitCode.GATE_REJECTED] = NormativeExitCode.GATE_REJECTED


class SchemaUsageError(_BaseEvalError):
    kind: Literal["schema_usage"] = "schema_usage"
    exit_code: Literal[NormativeExitCode.SCHEMA_USAGE] = NormativeExitCode.SCHEMA_USAGE


class CredentialUnavailableError(_BaseEvalError):
    kind: Literal["credential_unavailable"] = "credential_unavailable"
    exit_code: Literal[NormativeExitCode.CREDENTIAL_UNAVAILABLE] = (
        NormativeExitCode.CREDENTIAL_UNAVAILABLE
    )


class BillingGuardError(_BaseEvalError):
    kind: Literal["billing_guard"] = "billing_guard"
    exit_code: Literal[NormativeExitCode.BILLING_GUARD] = NormativeExitCode.BILLING_GUARD
    offending_vars: tuple[str, ...] = ()


class IsolationTamperError(_BaseEvalError):
    kind: Literal["isolation_tamper"] = "isolation_tamper"
    exit_code: Literal[NormativeExitCode.ISOLATION_TAMPER] = NormativeExitCode.ISOLATION_TAMPER


class VerifierCassetteError(_BaseEvalError):
    kind: Literal["verifier_cassette"] = "verifier_cassette"
    exit_code: Literal[NormativeExitCode.VERIFIER_CASSETTE] = NormativeExitCode.VERIFIER_CASSETTE


class QuotaCensoredError(_BaseEvalError):
    kind: Literal["quota_censored"] = "quota_censored"
    exit_code: Literal[NormativeExitCode.QUOTA_CENSORED] = NormativeExitCode.QUOTA_CENSORED


class MultiplexerError(_BaseEvalError):
    kind: Literal["multiplexer"] = "multiplexer"
    exit_code: Literal[NormativeExitCode.MULTIPLEXER] = NormativeExitCode.MULTIPLEXER


class CliUsageError(_BaseEvalError):
    kind: Literal["cli_usage"] = "cli_usage"
    exit_code: Literal[NormativeExitCode.CLI_USAGE] = NormativeExitCode.CLI_USAGE


class SplitDataError(_BaseEvalError):
    kind: Literal["split_data"] = "split_data"
    exit_code: Literal[NormativeExitCode.DATA_SPLIT_ERROR] = NormativeExitCode.DATA_SPLIT_ERROR


class AdapterUnavailableError(_BaseEvalError):
    kind: Literal["adapter_unavailable"] = "adapter_unavailable"
    exit_code: Literal[NormativeExitCode.ADAPTER_UNAVAILABLE] = (
        NormativeExitCode.ADAPTER_UNAVAILABLE
    )
    adapter_name: NonEmptyStr
    install_extra: NonEmptyStr


EvalError = Annotated[
    GateRejectedError
    | SchemaUsageError
    | CredentialUnavailableError
    | BillingGuardError
    | IsolationTamperError
    | VerifierCassetteError
    | QuotaCensoredError
    | MultiplexerError
    | CliUsageError
    | SplitDataError
    | AdapterUnavailableError,
    Field(discriminator="kind"),
]

type EvalResult[T] = Result[T, EvalError]


def map_error_to_exit_code(err: EvalError) -> NormativeExitCode:
    """Exhaustive 1-to-1 exit-code projection verified statically by basedpyright & mypy."""
    match err:
        case (
            GateRejectedError()
            | SchemaUsageError()
            | CredentialUnavailableError()
            | BillingGuardError()
            | IsolationTamperError()
            | VerifierCassetteError()
            | QuotaCensoredError()
            | MultiplexerError()
            | CliUsageError()
            | SplitDataError()
            | AdapterUnavailableError()
        ):
            return err.exit_code
        case unreachable:
            assert_never(unreachable)


def parse_model[T: FrozenModel](model_cls: type[T], raw: object) -> EvalResult[T]:
    """Boundary parser turning untrusted payloads into EvalResult[T] without leaking raw inputs."""
    try:
        return Ok(model_cls.model_validate(raw))
    except ValidationError:
        return Error(
            SchemaUsageError(
                reason_code="schema_validation_failed",
                message=static_redacted_literal("Input payload failed strict schema validation"),
            )
        )


class OkEnvelope[T: FrozenModel](FrozenModel):
    schema_version: Literal["harness-eval-envelope/v1"] = "harness-eval-envelope/v1"
    ok: Literal[True] = True
    command: SafeId
    exit_code: Literal[NormativeExitCode.OK] = NormativeExitCode.OK
    mutations: MutationScope = "none"
    data: T


class ErrEnvelope(FrozenModel):
    schema_version: Literal["harness-eval-envelope/v1"] = "harness-eval-envelope/v1"
    ok: Literal[False] = False
    command: SafeId
    exit_code: FailureExitCode
    reason_code: NonEmptyStr
    mutations: MutationScope = "none"
    error: RedactedStr
    details: PersistentMap[str, RedactedJsonValue] = Field(default_factory=empty_persistent_map)
    log_paths: tuple[RelativeRepoPath | ConfinedScratchPath, ...] = ()
    redacted: Literal[True] = True

    @classmethod
    def from_eval_error(
        cls,
        command: SafeId,
        err: EvalError,
        *,
        mutations: MutationScope = "none",
    ) -> ErrEnvelope:
        return cls(
            command=command,
            exit_code=err.exit_code,
            reason_code=err.reason_code,
            mutations=mutations,
            error=err.message,
            details=err.details,
            log_paths=err.log_paths,
        )


type Envelope[T: FrozenModel] = OkEnvelope[T] | ErrEnvelope
