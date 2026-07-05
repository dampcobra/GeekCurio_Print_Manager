import sqlite3
from datetime import datetime, timezone
from decimal import Decimal

from geekcurio_print_manager.models.print_job import FilamentUsage, PlateSummary, PrintJob
from geekcurio_print_manager.models.pricing_profile import PricingProfile
from geekcurio_print_manager.models.quote import QuoteBreakdown
from geekcurio_print_manager.models.saved_quote import SavedQuote


class QuoteRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(
        self,
        job: PrintJob,
        breakdown: QuoteBreakdown,
        profile: PricingProfile,
        notes: str | None = None,
    ) -> SavedQuote:
        created_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        cursor = self._conn.execute(
            """
            INSERT INTO quotes (
                quote_ref, created_at, source_file, slicer,
                profile_name, profile_label,
                print_time_s, total_weight_g,
                print_time_cost, material_cost, overhead_multiplier,
                markup_percentage, subtotal, markup_amount, total,
                notes
            ) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                job.source_path.name,
                job.slicer,
                profile.name,
                profile.label,
                job.total_print_time_s,
                job.total_weight_g,
                str(breakdown.print_time_cost),
                str(breakdown.material_cost),
                str(breakdown.overhead_multiplier),
                str(breakdown.markup_percentage),
                str(breakdown.subtotal),
                str(breakdown.markup_amount),
                str(breakdown.total),
                notes,
            ),
        )
        quote_id = cursor.lastrowid
        year = int(created_at[:4])
        quote_ref = f"GCQ-{year}-{quote_id:06d}"
        self._conn.execute("UPDATE quotes SET quote_ref = ? WHERE id = ?", (quote_ref, quote_id))

        for plate in job.plates:
            plate_cursor = self._conn.execute(
                """
                INSERT INTO quote_plates (quote_id, plate_index, print_time_s, weight_g, support_used, printer_model_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    quote_id,
                    plate.index,
                    plate.print_time_s,
                    plate.weight_g,
                    int(plate.support_used) if plate.support_used is not None else None,
                    plate.printer_model_id,
                ),
            )
            plate_id = plate_cursor.lastrowid
            for filament in plate.filaments:
                self._conn.execute(
                    """
                    INSERT INTO quote_plate_filaments (plate_id, filament_id, type, color, used_g, used_m)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (plate_id, filament.filament_id, filament.type, filament.color, filament.used_g, filament.used_m),
                )

        self._conn.commit()

        return SavedQuote(
            quote_ref=quote_ref,
            created_at=created_at,
            source_file=job.source_path.name,
            slicer=job.slicer,
            profile_name=profile.name,
            profile_label=profile.label,
            breakdown=breakdown,
            plates=job.plates,
            notes=notes,
        )

    def get_by_ref(self, quote_ref: str) -> SavedQuote | None:
        row = self._conn.execute(
            "SELECT * FROM quotes WHERE quote_ref = ?", (quote_ref,)
        ).fetchone()
        if row is None:
            return None
        return self._load_quote(row)

    def list_recent(self, n: int = 10) -> list[SavedQuote]:
        rows = self._conn.execute(
            "SELECT * FROM quotes ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
        return [self._load_quote(row) for row in rows]

    def _load_quote(self, row: sqlite3.Row) -> SavedQuote:
        breakdown = QuoteBreakdown(
            print_time_hours=float(Decimal(row["print_time_s"]) / Decimal("3600")),
            print_time_cost=Decimal(row["print_time_cost"]),
            material_weight_g=row["total_weight_g"],
            material_cost=Decimal(row["material_cost"]),
            overhead_multiplier=Decimal(row["overhead_multiplier"]),
            markup_percentage=Decimal(row["markup_percentage"]),
            subtotal=Decimal(row["subtotal"]),
            markup_amount=Decimal(row["markup_amount"]),
            total=Decimal(row["total"]),
        )
        return SavedQuote(
            quote_ref=row["quote_ref"],
            created_at=row["created_at"],
            source_file=row["source_file"],
            slicer=row["slicer"],
            profile_name=row["profile_name"],
            profile_label=row["profile_label"],
            breakdown=breakdown,
            plates=self._load_plates(row["id"]),
            notes=row["notes"],
        )

    def _load_plates(self, quote_id: int) -> tuple[PlateSummary, ...]:
        plate_rows = self._conn.execute(
            "SELECT * FROM quote_plates WHERE quote_id = ? ORDER BY plate_index",
            (quote_id,),
        ).fetchall()

        plates = []
        for plate_row in plate_rows:
            filament_rows = self._conn.execute(
                "SELECT * FROM quote_plate_filaments WHERE plate_id = ? ORDER BY filament_id",
                (plate_row["id"],),
            ).fetchall()
            filaments = tuple(
                FilamentUsage(
                    filament_id=f["filament_id"],
                    type=f["type"],
                    color=f["color"],
                    used_g=f["used_g"],
                    used_m=f["used_m"],
                )
                for f in filament_rows
            )
            support_val = plate_row["support_used"]
            plates.append(PlateSummary(
                index=plate_row["plate_index"],
                print_time_s=plate_row["print_time_s"],
                weight_g=plate_row["weight_g"],
                filaments=filaments,
                support_used=None if support_val is None else bool(support_val),
                printer_model_id=plate_row["printer_model_id"],
            ))
        return tuple(plates)
