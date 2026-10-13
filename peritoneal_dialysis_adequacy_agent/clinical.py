"""Transparent teaching calculations for adult chronic peritoneal dialysis.

These numerical outputs are not prescriptions or stand-alone adequacy assessments.
Sample concentrations within a calculation must use matching units.

References:
- ISPD membrane dysfunction recommendations (2021), doi:10.1177/0896860820982218
- ISPD goal-directed PD recommendations (2020), doi:10.1177/0896860819895364
"""
from __future__ import annotations

import math


def _number(name: str, value: float, *, positive: bool = False) -> float:
    try:
        number = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not math.isfinite(number) or (number <= 0 if positive else number < 0):
        rule = "positive" if positive else "non-negative"
        raise ValueError(f"{name} must be a finite {rule} number")
    return number


def pet_creatinine(dialysate_creatinine: float, plasma_creatinine: float) -> dict:
    """Compute 4-hour PET D/P creatinine with illustrative historical categories.

    The cutoffs are conventional historical descriptive bands, not universal
    ISPD diagnostic thresholds. Center-specific PET protocols take precedence.
    """
    dialysate = _number("4-hour dialysate creatinine", dialysate_creatinine)
    plasma = _number("plasma creatinine", plasma_creatinine, positive=True)
    ratio = dialysate / plasma
    if ratio > 1:
        raise ValueError("D/P creatinine exceeds 1; verify sampling, units and assay correction")
    # Classify the same four-decimal value that is reported to the user.
    band_ratio = round(ratio, 4)
    if band_ratio < 0.50:
        category = "Low"
    elif band_ratio < 0.65:
        category = "Low-average"
    elif band_ratio < 0.81:
        category = "High-average"
    else:
        category = "High"
    return {
        "dp_creatinine_4h": round(ratio, 4),
        "historical_transport_category": category,
        "interpretation": (
            "Descriptive historical 4-hour PET category only; not a diagnosis. "
            "Use local reference data and a glucose-corrected standardized PET protocol."
        ),
    }


def weekly_ktv(
    serum_urea: float,
    dialysate_urea: float,
    daily_drain_volume_l: float,
    urea_distribution_volume_l: float,
    urine_urea: float | None = None,
    daily_urine_volume_l: float | None = None,
) -> dict:
    """Calculate total weekly urea Kt/V using 24-hour collections.

    V is urea distribution volume in litres. All urea concentrations must use
    identical units. Renal component is optional but requires both measurements.
    """
    serum = _number("serum urea", serum_urea, positive=True)
    dialysate = _number("dialysate urea", dialysate_urea)
    drain = _number("24-hour drain volume (L)", daily_drain_volume_l)
    volume = _number("urea distribution volume (L)", urea_distribution_volume_l, positive=True)

    if (urine_urea is None) != (daily_urine_volume_l is None):
        raise ValueError("Provide both urine urea and 24-hour urine volume, or neither")
    peritoneal = (dialysate / serum) * drain * 7 / volume
    renal = 0.0
    if urine_urea is not None:
        urine_concentration = _number("urine urea", urine_urea)
        urine_volume = _number("24-hour urine volume (L)", daily_urine_volume_l)
        renal = (urine_concentration / serum) * urine_volume * 7 / volume
    if not all(math.isfinite(x) for x in (peritoneal, renal, peritoneal + renal)):
        raise ValueError("calculated weekly Kt/V exceeds the finite numeric range")
    return {
        "peritoneal_weekly_ktv": round(peritoneal, 4),
        "renal_weekly_ktv": round(renal, 4),
        "total_weekly_ktv": round(peritoneal + renal, 4),
        "interpretation": (
            "Urea clearance estimate, not a sufficient measure of dialysis adequacy. "
            "Interpret alongside symptoms, volume status, residual kidney function, "
            "biochemistry and individual treatment goals (ISPD 2020)."
        ),
    }
