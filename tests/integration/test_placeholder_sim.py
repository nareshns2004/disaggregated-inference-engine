"""M3: coordinator + SimTransport end-to-end (CPU). Fault classes K01-K03, K10 in simulation."""

import pytest


@pytest.mark.skip(reason="M3: needs kvwire.sim")
def test_happy_path_sim() -> None: ...
