import { test } from "node:test";
import assert from "node:assert/strict";
import { pet, ktv } from "../web/calculations.mjs";

test("historical PET boundaries and ratio", () => {
  assert.equal(pet(6.8, 10).dp_creatinine_4h, 0.68);
  for (const [d, label] of [
    [4.9, "Low"], [5, "Low-average"], [6.49, "Low-average"],
    [6.5, "High-average"], [8.09, "High-average"], [8.1, "High"]
  ]) {
    assert.equal(pet(d, 10).historical_transport_category, label);
  }
});
test("PET rejects invalid and impossible ratios", () => {
  for (const [d, p] of [[-1, 10], [4, 0], [4, Infinity], [NaN, 10], [11, 10], ["", 10]]) {
    assert.throws(() => pet(d, p));
  }
});
test("renal and peritoneal weekly Kt/V match independent arithmetic", () => {
  const input = {
    serum_urea: 50, dialysate_urea: 40,
    daily_drain_volume_l: 10, urea_distribution_volume_l: 40
  };
  assert.deepEqual(
    [ktv(input).peritoneal_weekly_ktv, ktv(input).total_weekly_ktv],
    [1.4, 1.4]
  );
  const withUrine = ktv({...input, urine_urea: 150, daily_urine_volume_l: .5});
  assert.equal(withUrine.renal_weekly_ktv, .2625);
  assert.equal(withUrine.total_weekly_ktv, 1.6625);
});
test("missing urine pair, negative and overflowing values rejected", () => {
  const input = {
    serum_urea: 50, dialysate_urea: 40,
    daily_drain_volume_l: 10, urea_distribution_volume_l: 40
  };
  for (const extras of [
    {urine_urea: 150},
    {daily_urine_volume_l: 1},
    {urine_urea: -1, daily_urine_volume_l: 1},
    {serum_urea: 0},
    {daily_drain_volume_l: ""},
    {daily_drain_volume_l: -1},
    {dialysate_urea: Infinity},
    {dialysate_urea: 1e308, daily_drain_volume_l: 1e308}
  ]) assert.throws(() => ktv({...input,...extras}));
});
