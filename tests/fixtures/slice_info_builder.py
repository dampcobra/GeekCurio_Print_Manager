import io
import zipfile

METADATA_KEYS = ("index", "prediction", "weight", "outside", "support_used", "printer_model_id")


def _build_slice_info_xml(plates: list[dict]) -> str:
    plate_blocks = []
    for plate in plates:
        metadata_tags = "".join(
            f'<metadata key="{key}" value="{plate[key]}"/>'
            for key in METADATA_KEYS
            if key in plate
        )
        filament_tags = "".join(
            "<filament " + " ".join(f'{attr}="{value}"' for attr, value in filament.items()) + "/>"
            for filament in plate.get("filaments", [])
        )
        plate_blocks.append(f"<plate>{metadata_tags}{filament_tags}</plate>")
    return '<?xml version="1.0" encoding="UTF-8"?><config>' + "".join(plate_blocks) + "</config>"


def build_fake_3mf(
    plates: list[dict] | None = None,
    *,
    sliced: bool = True,
    valid_skeleton: bool = True,
    slice_info_override: str | None = None,
) -> io.BytesIO:
    """Build a minimal in-memory .3mf archive for tests.

    - `plates`: list of dicts describing <plate> metadata/filaments (see METADATA_KEYS).
    - `sliced=False`: omit Metadata/slice_info.config entirely (unsliced project file).
    - `valid_skeleton=False`: omit the [Content_Types].xml / 3D/3dmodel.model 3MF skeleton.
    - `slice_info_override`: write this raw string as slice_info.config instead of building one
      (used to test malformed XML).
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        if valid_skeleton:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr("3D/3dmodel.model", "<model/>")
        if slice_info_override is not None:
            archive.writestr("Metadata/slice_info.config", slice_info_override)
        elif sliced:
            archive.writestr("Metadata/slice_info.config", _build_slice_info_xml(plates or []))
    buffer.seek(0)
    return buffer
