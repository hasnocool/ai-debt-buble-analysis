// src/ai_debt_bubble_analysis/static/app.js
const $ = (id) => document.getElementById(id);

function money(value) {
  if (value == null || Number.isNaN(value)) return "—";
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  const units = [[1e12, "T"], [1e9, "B"], [1e6, "M"]];
  for (const [scale, suffix] of units) {
    if (abs >= scale) return sign + (abs / scale).toFixed(1) + suffix;
  }
  return sign + abs.toFixed(0);
}
function pct(value) {
  return value == null ? "—" : (value * 100).toFixed(1) + "%";
}
function riskClass(value) {
  if (value >= 70) return "metric-bad";
  if (value >= 45) return "metric-warn";
  return "metric-good";
}

function drawBars(canvas, companies) {
  const ctx = canvas.getContext("2d");
  const width = canvas.width, height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  const margin = 45;
  const max = Math.max(...companies.map(c => c.ai_weighted_market_cap || 0), 1);
  const row = (height - margin * 2) / Math.max(companies.length, 1);

  ctx.font = "12px monospace";
  companies.forEach((company, i) => {
    const y = margin + i * row + 10;
    const value = company.ai_weighted_market_cap || 0;
    const bar = (width - 260) * (value / max);
    ctx.fillStyle = "#00ff66";
    ctx.fillRect(150, y, bar, Math.max(10, row - 12));
    ctx.fillStyle = "#f3f7f4";
    ctx.fillText(company.ticker, 8, y + 10);
    ctx.fillText(money(value), Math.min(width - 85, 158 + bar), y + 10);
  });
}

function render(data) {
  $("market-value").textContent = money(data.monitored_market_cap);
  $("wealth-20").textContent = money(data.wealth_at_20);
  $("top1").textContent = data.top1_concentration_pct.toFixed(1) + "%";
  $("macro").textContent = data.macro.stress_score.toFixed(1) + "/100";
  $("hhi").textContent = data.hhi.toFixed(0);
  $("updated").textContent = new Date(data.generated_at).toLocaleString();

  $("alerts").innerHTML = (data.alerts || []).map(alert => `
    <div class="alert ${alert.severity}">
      <strong>${alert.title}</strong>
      <span>${alert.detail}</span>
    </div>
  `).join("");

  $("company-table").innerHTML = data.companies.map(company => `
    <tr>
      <td>${company.ticker}</td>
      <td>${money(company.market_cap)}</td>
      <td>${pct(company.debt_to_assets)}</td>
      <td class="${riskClass(company.commitment_score)}">${company.commitment_score.toFixed(1)}</td>
      <td>${pct(company.return_1y)}</td>
      <td>${pct(company.max_drawdown)}</td>
      <td class="${riskClass(company.risk_score)}">${company.risk_score.toFixed(1)}</td>
    </tr>
  `).join("");

  const macroNames = {
    SP500: "S&P 500",
    VIXCLS: "VIX",
    DGS10: "10Y Treasury",
    BAMLH0A0HYM2: "High-yield spread",
    STLFSI4: "Financial stress",
  };
  $("macro-table").innerHTML = Object.entries(data.macro.series).map(([key, value]) => `
    <div class="signal">
      <b>${macroNames[key] || key}</b>
      <span>
        latest: ${value.latest == null ? "—" : value.latest.toFixed(2)}
        &nbsp; / &nbsp; 1Y delta: ${value.one_year_change == null ? "—" : value.one_year_change.toFixed(2)}
        &nbsp; / &nbsp; z: ${value.z_score == null ? "—" : value.z_score.toFixed(2)}
      </span>
    </div>
  `).join("");

  $("evidence").innerHTML = data.companies.map(company => `
    <div class="evidence-item">
      <div class="evidence-head">
        <strong>${company.ticker}</strong>
        <span>score ${company.commitment_score.toFixed(1)} • ${company.commitment_mentions} mentions • ${company.filing.filed_at || "filing date unavailable"}</span>
      </div>
      ${company.filing.url ? `<div class="snippet"><a href="${company.filing.url}" target="_blank" rel="noreferrer" style="color:#42d9ff">open 10-K</a></div>` : ""}
      ${(company.filing.snippets || []).slice(0, 3).map(snippet => `<div class="snippet">${snippet}</div>`).join("")}
    </div>
  `).join("");

  drawBars($("wealth-chart"), data.companies);
}

async function load(force = false) {
  $("refresh").disabled = true;
  $("refresh").textContent = "Refreshing…";
  try {
    const response = await fetch(force ? "/api/refresh" : "/api/overview", {
      method: force ? "POST" : "GET",
      cache: "no-store",
    });
    const data = await response.json();
    render(data);
  } catch (error) {
    $("alerts").innerHTML = `<div class="alert high"><strong>Data refresh failed</strong><span>${error}</span></div>`;
  } finally {
    $("refresh").disabled = false;
    $("refresh").textContent = "Refresh evidence";
  }
}

$("refresh").addEventListener("click", () => load(true));
load(false);
setInterval(() => load(false), 5 * 60 * 1000);
