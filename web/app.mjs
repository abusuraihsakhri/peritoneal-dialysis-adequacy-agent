import { pet, ktv } from "./calculations.mjs";

const results = {};
const downloadButton = document.getElementById("export");
const get = id => document.getElementById(id).value;

function clearResult(id, key) {
  delete results[key];
  const node = document.getElementById(id);
  node.replaceChildren();
  const message = document.createElement("span");
  message.className = "muted";
  message.textContent = "Enter collection values and calculate.";
  node.append(message);
  downloadButton.disabled = Object.keys(results).length === 0;
}

function showError(id, err) {
  const node = document.getElementById(id);
  node.replaceChildren();
  const message = document.createElement("p");
  message.className = "error";
  message.textContent = err.message || "Invalid data.";
  node.append(message);
}

function render(id, key, data, pairs) {
  results[key] = data;
  const node = document.getElementById(id);
  node.replaceChildren();
  const row = document.createElement("div");
  row.className = "data-row";
  for (const [label, value] of pairs) {
    const item = document.createElement("div");
    const number = document.createElement("div");
    number.className = "number";
    number.textContent = String(value);
    const caption = document.createElement("small");
    caption.textContent = label;
    item.append(number, caption);
    row.append(item);
  }
  const note = document.createElement("p");
  note.className = "hint";
  note.textContent = data.interpretation;
  node.append(row, note);
  downloadButton.disabled = false;
}

document.getElementById("pet-form").addEventListener("submit", event => {
  event.preventDefault();
  try {
    const data = pet(get("pet-d"), get("pet-p"));
    render("pet-result", "pet", data, [
      ["D/P creatinine (4 h)", data.dp_creatinine_4h],
      ["Historical category", data.historical_transport_category]
    ]);
  } catch (error) {
    delete results.pet;
    showError("pet-result", error);
    downloadButton.disabled = Object.keys(results).length === 0;
  }
});
document.getElementById("ktv-form").addEventListener("submit", event => {
  event.preventDefault();
  try {
    const data = ktv({
      serum_urea: get("serum"),
      dialysate_urea: get("dialysate"),
      daily_drain_volume_l: get("drain"),
      urea_distribution_volume_l: get("volume"),
      urine_urea: get("urine"),
      daily_urine_volume_l: get("urine-volume")
    });
    render("ktv-result", "ktv", data, [
      ["Peritoneal / week", data.peritoneal_weekly_ktv],
      ["Residual renal / week", data.renal_weekly_ktv],
      ["Total weekly Kt/V", data.total_weekly_ktv]
    ]);
  } catch (error) {
    delete results.ktv;
    showError("ktv-result", error);
    downloadButton.disabled = Object.keys(results).length === 0;
  }
});
document.getElementById("pet-form").addEventListener("reset", () => clearResult("pet-result", "pet"));
document.getElementById("ktv-form").addEventListener("reset", () => clearResult("ktv-result", "ktv"));

downloadButton.addEventListener("click", () => {
  if (!Object.keys(results).length) return;
  const blob = new Blob([JSON.stringify({
    calculations: results,
    note: "Educational synthetic-input calculations only; not a clinical adequacy assessment."
  }, null, 2)], {type:"application/json"});
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "pd-adequacy-results.json";
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 500);
});
