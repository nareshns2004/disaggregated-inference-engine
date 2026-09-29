from __future__ import annotations

import pytest

from kvwire.coordinator.state_machine import (
    LEGAL_TRANSITIONS,
    TERMINAL,
    IllegalTransitionError,
    TransferState,
    check_transition,
)

S = TransferState


def test_every_state_has_an_entry() -> None:
    assert set(LEGAL_TRANSITIONS) == set(TransferState)


def test_terminal_states_have_no_exits() -> None:
    for s in TERMINAL:
        assert not LEGAL_TRANSITIONS[s]


def test_every_non_terminal_live_state_can_abort() -> None:
    for s in (S.RESERVED, S.STREAMING, S.COMMITTED, S.DECODING):
        assert S.ABORTED in LEGAL_TRANSITIONS[s]


def test_cannot_skip_commit() -> None:
    with pytest.raises(IllegalTransitionError):
        check_transition(S.STREAMING, S.DECODING)
