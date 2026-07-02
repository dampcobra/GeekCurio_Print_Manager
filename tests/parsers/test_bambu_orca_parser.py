import zipfile
from pathlib import Path

import pytest

from geekcurio_print_manager.exceptions import SliceMetadataParseError
from geekcurio_print_manager.parsers.bambu_orca import BambuOrcaParser
from tests.fixtures.slice_info_builder import build_fake_3mf

SOURCE_PATH = Path("test.3mf")


def test_single_plate_parses(single_plate_3mf):
    with zipfile.ZipFile(single_plate_3mf) as archive:
        parser = BambuOrcaParser()
        assert parser.can_parse(archive)
        job = parser.parse(archive, SOURCE_PATH)

    assert len(job.plates) == 1
    plate = job.plates[0]
    assert plate.index == 1
    assert plate.print_time_s == 4823
    assert plate.weight_g == pytest.approx(18.46)
    assert plate.support_used is False
    assert plate.printer_model_id == "C13"
    assert len(plate.filaments) == 2
    assert plate.filaments[0].type == "PLA"
    assert plate.filaments[0].used_g == pytest.approx(14.21)


def test_multi_plate_parses(multi_plate_3mf):
    with zipfile.ZipFile(multi_plate_3mf) as archive:
        job = BambuOrcaParser().parse(archive, SOURCE_PATH)

    assert [plate.index for plate in job.plates] == [1, 2]
    assert job.total_print_time_s == 4823 + 3600
    assert job.total_weight_g == pytest.approx(18.46 + 10.0)


def test_cannot_parse_unsliced_archive(unsliced_3mf):
    with zipfile.ZipFile(unsliced_3mf) as archive:
        assert not BambuOrcaParser().can_parse(archive)


def test_missing_prediction_raises():
    buffer = build_fake_3mf([{"index": "1", "weight": "10.0"}])
    with zipfile.ZipFile(buffer) as archive:
        with pytest.raises(SliceMetadataParseError):
            BambuOrcaParser().parse(archive, SOURCE_PATH)


def test_missing_weight_raises():
    buffer = build_fake_3mf([{"index": "1", "prediction": "100"}])
    with zipfile.ZipFile(buffer) as archive:
        with pytest.raises(SliceMetadataParseError):
            BambuOrcaParser().parse(archive, SOURCE_PATH)


def test_non_numeric_weight_raises():
    buffer = build_fake_3mf([{"index": "1", "prediction": "100", "weight": "not-a-number"}])
    with zipfile.ZipFile(buffer) as archive:
        with pytest.raises(SliceMetadataParseError):
            BambuOrcaParser().parse(archive, SOURCE_PATH)


def test_malformed_xml_raises():
    buffer = build_fake_3mf(slice_info_override="<config><plate>unclosed")
    with zipfile.ZipFile(buffer) as archive:
        with pytest.raises(SliceMetadataParseError):
            BambuOrcaParser().parse(archive, SOURCE_PATH)


def test_no_plates_raises():
    buffer = build_fake_3mf(slice_info_override='<?xml version="1.0"?><config></config>')
    with zipfile.ZipFile(buffer) as archive:
        with pytest.raises(SliceMetadataParseError):
            BambuOrcaParser().parse(archive, SOURCE_PATH)


def test_filament_missing_type_raises():
    buffer = build_fake_3mf(
        [
            {
                "index": "1",
                "prediction": "100",
                "weight": "10.0",
                "filaments": [{"id": "1", "used_g": "10.0"}],
            }
        ]
    )
    with zipfile.ZipFile(buffer) as archive:
        with pytest.raises(SliceMetadataParseError):
            BambuOrcaParser().parse(archive, SOURCE_PATH)
