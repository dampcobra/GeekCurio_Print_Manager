import pytest

from geekcurio_print_manager.exceptions import (
    InvalidProjectArchiveError,
    ProjectFileNotFoundError,
    SliceMetadataNotFoundError,
)
from geekcurio_print_manager.services.inspection_service import InspectionService


def test_nonexistent_path_raises(tmp_path):
    service = InspectionService()
    with pytest.raises(ProjectFileNotFoundError):
        service.inspect(tmp_path / "does_not_exist.3mf")


def test_corrupt_zip_raises(make_3mf_file, corrupt_zip_bytes):
    path = make_3mf_file(corrupt_zip_bytes)
    service = InspectionService()
    with pytest.raises(InvalidProjectArchiveError):
        service.inspect(path)


def test_non_3mf_zip_raises(make_3mf_file, not_a_3mf_zip):
    path = make_3mf_file(not_a_3mf_zip)
    service = InspectionService()
    with pytest.raises(InvalidProjectArchiveError):
        service.inspect(path)


def test_unsliced_project_raises(make_3mf_file, unsliced_3mf):
    path = make_3mf_file(unsliced_3mf)
    service = InspectionService()
    with pytest.raises(SliceMetadataNotFoundError):
        service.inspect(path)


def test_happy_path_returns_print_job(make_3mf_file, single_plate_3mf):
    path = make_3mf_file(single_plate_3mf)
    service = InspectionService()

    job = service.inspect(path)

    assert job.source_path == path
    assert job.total_print_time_s == 4823
    assert job.total_weight_g == pytest.approx(18.46)
