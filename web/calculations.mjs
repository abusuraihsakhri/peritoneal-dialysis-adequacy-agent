// Browser counterpart of peritoneal_dialysis_adequacy_agent/clinical.py.
// Educational calculations only; not a clinical prescription.
function finite(name, value, positive = false) {
  if (value === "" || value === null || value === undefined) {
    throw new Error(name + " is required.");
  }
  const n = Number(value);
  if (!Number.isFinite(n) || (positive ? n <= 0 : n < 0)) {
    throw new Error(name + " must be a finite " + (positive ? "positive" : "non-negative") + " number.");
  }
  return n;
}
const round4 = n => Math.round((n + Number.EPSILON) * 10000) / 10000;

export function pet(dialysateCreatinine, plasmaCreatinine) {
  const d = finite("4-hour dialysate creatinine", dialysateCreatinine);
  const p = finite("plasma creatinine", plasmaCreatinine, true);
  const ratio = d / p;
  if (ratio > 1) {
    throw new Error("D/P creatinine exceeds 1; verify sampling, units and assay correction.");
  }
  const category = ratio < .50 ? "Low"
    : ratio < .65 ? "Low-average"
    : ratio < .81 ? "High-average" : "High";
  return {
    dp_creatinine_4h: round4(ratio),
    historical_transport_category: category,
    interpretation: "Descriptive historical 4-hour PET category only; not a diagnosis. Use local reference data and a glucose-corrected standardized PET protocol."
  };
}

export function ktv({
  serum_urea, dialysate_urea, daily_drain_volume_l,
  urea_distribution_volume_l, urine_urea = null, daily_urine_volume_l = null
}) {
  const s = finite("serum urea", serum_urea, true);
  const d = finite("dialysate urea", dialysate_urea);
  const drain = finite("24-hour drain volume (L)", daily_drain_volume_l);
  const v = finite("urea distribution volume (L)", urea_distribution_volume_l, true);
  const hasUrine = urine_urea !== null && urine_urea !== "";
  const hasVolume = daily_urine_volume_l !== null && daily_urine_volume_l !== "";
  if (hasUrine !== hasVolume) {
    throw new Error("Provide both urine urea and 24-hour urine volume, or neither.");
  }
  const peritoneal = 7 * d / s * drain / v;
  const renal = hasUrine ? 7 * finite("urine urea", urine_urea) / s
    * finite("24-hour urine volume (L)", daily_urine_volume_l) / v : 0;
  if (![peritoneal, renal, peritoneal + renal].every(Number.isFinite)) {
    throw new Error("Calculated weekly Kt/V exceeds the finite numeric range.");
  }
  return {
    peritoneal_weekly_ktv: round4(peritoneal),
    renal_weekly_ktv: round4(renal),
    total_weekly_ktv: round4(peritoneal + renal),
    interpretation: "Urea clearance estimate, not a sufficient measure of dialysis adequacy. Interpret alongside symptoms, volume status, residual kidney function, biochemistry and individual treatment goals (ISPD 2020)."
  };
}
