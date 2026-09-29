import pytest


@pytest.mark.multinode
def test_k07_late_write_is_rejected() -> None:
    pytest.skip("M2: FAULT_MATRIX K07 on real hardware; zero corruption required")
