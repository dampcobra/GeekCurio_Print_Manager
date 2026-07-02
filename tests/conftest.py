import io
from pathlib import Path

import pytest

from tests.fixtures.slice_info_builder import build_fake_3mf


@pytest.fixture
def single_plate_3mf() -> io.BytesIO:
    return build_fake_3mf(
        [
            {
                "index": "1",
                "prediction": "4823",
                "weight": "18.46",
                "support_used": "false",
                "printer_model_id": "C13",
                "filaments": [
                    {"id": "1", "type": "PLA", "color": "#FF0000", "used_g": "14.21", "used_m": "4.823"},
                    {"id": "2", "type": "PLA", "color": "#00FF00", "used_g": "4.25", "used_m": "1.412"},
                ],
            }
        ]
    )


@pytest.fixture
def multi_plate_3mf() -> io.BytesIO:
    return build_fake_3mf(
        [
            {
                "index": "1",
                "prediction": "4823",
                "weight": "18.46",
                "filaments": [{"id": "1", "type": "PLA", "used_g": "18.46"}],
            },
            {
                "index": "2",
                "prediction": "3600",
                "weight": "10.0",
                "filaments": [{"id": "1", "type": "PETG", "used_g": "10.0"}],
            },
        ]
    )


@pytest.fixture
def unsliced_3mf() -> io.BytesIO:
    return build_fake_3mf(sliced=False)


@pytest.fixture
def corrupt_zip_bytes() -> io.BytesIO:
    return io.BytesIO(b"this is not a zip file")


@pytest.fixture
def not_a_3mf_zip() -> io.BytesIO:
    return build_fake_3mf(valid_skeleton=False, sliced=False)


@pytest.fixture
def make_3mf_file(tmp_path):
    def _make(buffer: io.BytesIO, filename: str = "test.3mf") -> Path:
        path = tmp_path / filename
        path.write_bytes(buffer.getvalue())
        return path

    return _make
