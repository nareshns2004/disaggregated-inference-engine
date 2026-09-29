import pytest


@pytest.mark.gpu
def test_gpu_mr_registration() -> None:
    pytest.skip("M2: register a cudaMalloc'd pool via dmabuf/peermem (ADR-0002)")
