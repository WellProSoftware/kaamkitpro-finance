"use client";

import { useEffect, useMemo, useState } from "react";

type Inputs = {
  projectName: string;
  projectType: string;
  projectCost: number;
  debtPct: number;
  monthlyRevenue: number;
  growthPct: number;
  variableCostPct: number;
  monthlyFixedCost: number;
  interestPct: number;
  loanYears: number;
  projectionYears: number;
};

const initial: Inputs = {
  projectName: "New Project",
  projectType: "Hospital",
  projectCost: 50000000,
  debtPct: 60,
  monthlyRevenue: 8000000,
  growthPct: 8,
  variableCostPct: 48,
  monthlyFixedCost: 2200000,
  interestPct: 11,
  loanYears: 7,
  projectionYears: 5,
};

const money = (value: number) => new Intl.NumberFormat("en-IN", {
  style: "currency", currency: "INR", maximumFractionDigits: 0,
}).format(Number.isFinite(value) ? value : 0);

export default function Home() {
  const [inputs, setInputs] = useState<Inputs>(initial);
  const [saved, setSaved] = useState(false);
  const [draftLoaded, setDraftLoaded] = useState(false);
  const [exportStatus, setExportStatus] = useState("");
  const [exporting, setExporting] = useState<"excel" | "pdf" | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("kaamkitpro-finance-draft");
      if (raw) {
        const parsed: unknown = JSON.parse(raw);
        if (parsed && typeof parsed === "object") {
          const draft = parsed as Partial<Inputs>;
          const validNumber = (value: unknown): value is number =>
            typeof value === "number" && Number.isFinite(value);
          if (
            typeof draft.projectName === "string" &&
            typeof draft.projectType === "string" &&
            validNumber(draft.projectCost) && draft.projectCost >= 0 &&
            validNumber(draft.debtPct) && draft.debtPct >= 0 && draft.debtPct <= 100 &&
            validNumber(draft.monthlyRevenue) && draft.monthlyRevenue >= 0 &&
            validNumber(draft.growthPct) && draft.growthPct >= -100 && draft.growthPct <= 500 &&
            validNumber(draft.variableCostPct) && draft.variableCostPct >= 0 && draft.variableCostPct <= 100 &&
            validNumber(draft.monthlyFixedCost) && draft.monthlyFixedCost >= 0 &&
            validNumber(draft.interestPct) && draft.interestPct >= 0 && draft.interestPct <= 100 &&
            validNumber(draft.loanYears) && Number.isInteger(draft.loanYears) && draft.loanYears >= 1 && draft.loanYears <= 30 &&
            validNumber(draft.projectionYears) && Number.isInteger(draft.projectionYears) && draft.projectionYears >= 1 && draft.projectionYears <= 100
          ) {
            setInputs({ ...initial, ...draft });
            setSaved(true);
          }
        }
      }
    } catch {
      // Ignore unavailable storage or invalid draft data and keep safe defaults.
    } finally {
      setDraftLoaded(true);
    }
  }, []);

  const update = (key: keyof Inputs, value: string) => {
    const numeric = ["projectCost","debtPct","monthlyRevenue","growthPct","variableCostPct","monthlyFixedCost","interestPct","loanYears","projectionYears"].includes(key);
    setInputs((prev) => ({ ...prev, [key]: numeric ? Number(value) : value }));
    setSaved(false);
  };

  const model = useMemo(() => {
    const debt = inputs.projectCost * inputs.debtPct / 100;
    const equity = inputs.projectCost - debt;
    const variableRate = Math.min(100, Math.max(0, inputs.variableCostPct)) / 100;
    const rows = Array.from({ length: Math.max(1, Math.min(100, inputs.projectionYears || 1)) }, (_, i) => {
      const year = i + 1;
      const revenue = inputs.monthlyRevenue * 12 * Math.pow(1 + inputs.growthPct / 100, i);
      const variableCost = revenue * variableRate;
      const fixedCost = inputs.monthlyFixedCost * 12;
      const ebitda = revenue - variableCost - fixedCost;
      const principal = year <= inputs.loanYears ? debt / Math.max(1, inputs.loanYears) : 0;
      const openingDebt = Math.max(0, debt - (year - 1) * debt / Math.max(1, inputs.loanYears));
      const interest = year <= inputs.loanYears ? openingDebt * inputs.interestPct / 100 : 0;
      const debtService = principal + interest;
      return { year, revenue, variableCost, fixedCost, ebitda, interest, principal, debtService,
        dscr: debtService > 0 ? ebitda / debtService : null,
        breakEven: variableRate < 1 ? fixedCost / (1 - variableRate) : null,
        cash: ebitda - debtService };
    });
    return { debt, equity, rows };
  }, [inputs]);

  const exportCsv = () => {
    const headers = ["Year","Revenue","Variable Cost","Fixed Cost","EBITDA","Interest","Principal","Debt Service","DSCR","Break-even Revenue","Cash After Debt Service"];
    const lines = [headers, ...model.rows.map((r) => [r.year,r.revenue,r.variableCost,r.fixedCost,r.ebitda,r.interest,r.principal,r.debtService,r.dscr ?? "",r.breakEven ?? "",r.cash])];
    const csv = lines.map((row) => row.map((v) => {
      const s = String(v ?? "");
      return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    }).join(",")).join("\r\n");
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "kaamkitpro-finance-projection.csv";
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const exportReport = async (format: "excel" | "pdf") => {
    const apiBase = process.env.NEXT_PUBLIC_FINANCE_API_URL?.trim().replace(/\/$/, "");
    if (!apiBase) {
      setExportStatus("Excel/PDF export is ready to connect, but the staging API URL is not configured yet. CSV export remains available.");
      return;
    }

    setExporting(format);
    setExportStatus("");
    const payload = {
      project_name: inputs.projectName,
      project_type: inputs.projectType,
      project_cost: inputs.projectCost,
      debt_pct: inputs.debtPct,
      monthly_revenue: inputs.monthlyRevenue,
      growth_pct: inputs.growthPct,
      variable_cost_pct: inputs.variableCostPct,
      monthly_fixed_cost: inputs.monthlyFixedCost,
      interest_pct: inputs.interestPct,
      loan_years: inputs.loanYears,
      projection_years: inputs.projectionYears,
    };

    try {
      const response = await fetch(`${apiBase}/api/reports/${format}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(response.status === 422
          ? "Please review the assumptions. The API rejected one or more values."
          : `Report service returned HTTP ${response.status}.`);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = format === "excel"
        ? "kaamkitpro-finance-projection.xlsx"
        : "kaamkitpro-finance-projection.pdf";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setExportStatus(`${format === "excel" ? "Excel" : "PDF"} report downloaded.`);
    } catch (error) {
      setExportStatus(error instanceof Error
        ? `Export failed: ${error.message}`
        : "Export failed. Check the staging API configuration and try again.");
    } finally {
      setExporting(null);
    }
  };

  const saveAssumptions = () => {
    try {
      localStorage.setItem("kaamkitpro-finance-draft", JSON.stringify(inputs));
      setSaved(true);
    } catch {
      setSaved(false);
    }
  };

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand"><div className="brandmark">K</div><div>KaamKitPro Finance<span className="subbrand">Project planning & financial modelling</span></div></div>
        <span className="pill">STAGING ENVIRONMENT</span>
      </header>

      <section className="hero">
        <div><div className="eyebrow">Financial planning workspace</div><h1>Turn your project into a clear financial plan.</h1><p>Build a practical first-pass projection for a hospital, pharmacy, optical store, retail business, warehouse or manufacturing project.</p></div>
        <div className="actions"><button className="secondary" onClick={saveAssumptions}>Save draft</button><button className="secondary" onClick={exportCsv}>Export CSV</button><button className="secondary" onClick={() => void exportReport("excel")} disabled={exporting !== null}>{exporting === "excel" ? "Preparing Excel…" : "Export Excel"}</button><button className="secondary" onClick={() => void exportReport("pdf")} disabled={exporting !== null}>{exporting === "pdf" ? "Preparing PDF…" : "Export PDF"}</button></div>
      </section>

      <div className="grid">
        <section className="card">
          <h2 className="section-title">Project assumptions</h2><p className="section-desc">Change any input to recalculate the projection instantly. Figures are in Indian rupees. Drafts stay in this browser.</p>
          <div className="fields">
            <div className="field full"><label htmlFor="projectName">Project name</label><input id="projectName" value={inputs.projectName} onChange={(e) => update("projectName", e.target.value)} maxLength={120}/></div>
            <div className="field full"><label htmlFor="projectType">Business type</label><select id="projectType" value={inputs.projectType} onChange={(e) => update("projectType", e.target.value)}>{["Hospital","Pharmacy","Optical","Retail","Warehouse","Manufacturing","Services","Other"].map(x=><option key={x}>{x}</option>)}</select></div>
            <div className="field"><label htmlFor="projectCost">Total project cost (₹)</label><div className="input-wrap"><span>₹</span><input id="projectCost" type="number" min="0" value={inputs.projectCost} onChange={(e) => update("projectCost", e.target.value)}/></div></div>
            <div className="field"><label htmlFor="debtPct">Loan funding (%)</label><input id="debtPct" type="number" min="0" max="100" value={inputs.debtPct} onChange={(e) => update("debtPct", e.target.value)}/></div>
            <div className="field"><label htmlFor="monthlyRevenue">Monthly revenue (₹)</label><div className="input-wrap"><span>₹</span><input id="monthlyRevenue" type="number" min="0" value={inputs.monthlyRevenue} onChange={(e) => update("monthlyRevenue", e.target.value)}/></div></div>
            <div className="field"><label htmlFor="growthPct">Annual revenue growth (%)</label><input id="growthPct" type="number" min="-100" max="500" value={inputs.growthPct} onChange={(e) => update("growthPct", e.target.value)}/></div>
            <div className="field"><label htmlFor="variableCostPct">Variable costs (%)</label><input id="variableCostPct" type="number" min="0" max="100" value={inputs.variableCostPct} onChange={(e) => update("variableCostPct", e.target.value)}/></div>
            <div className="field"><label htmlFor="monthlyFixedCost">Monthly fixed costs (₹)</label><div className="input-wrap"><span>₹</span><input id="monthlyFixedCost" type="number" min="0" value={inputs.monthlyFixedCost} onChange={(e) => update("monthlyFixedCost", e.target.value)}/></div></div>
            <div className="field"><label htmlFor="interestPct">Annual interest rate (%)</label><input id="interestPct" type="number" min="0" max="100" value={inputs.interestPct} onChange={(e) => update("interestPct", e.target.value)}/></div>
            <div className="field"><label htmlFor="loanYears">Loan tenure (years)</label><input id="loanYears" type="number" min="1" max="30" value={inputs.loanYears} onChange={(e) => update("loanYears", e.target.value)}/></div>
            <div className="field"><label htmlFor="projectionYears">Projection period (years, up to 100)</label><input id="projectionYears" type="number" min="1" max="100" step="1" value={inputs.projectionYears} onChange={(e) => update("projectionYears", e.target.value)}/></div>
          </div>
          <button className="primary" onClick={saveAssumptions}>Save project draft on this device</button>
          {draftLoaded && saved && <p className="section-desc" role="status" style={{marginTop:10,marginBottom:0}}>Draft restored or saved in this browser only. Account sync is not connected yet.</p>}
        </section>

        <section>
          <div className="stats">
            <div className="stat blue"><span>Total project cost</span><strong>{money(inputs.projectCost)}</strong><small>Initial project investment</small></div>
            <div className="stat"><span>Estimated loan</span><strong>{money(model.debt)}</strong><small>{inputs.debtPct}% of project cost</small></div>
            <div className="stat green"><span>Owner contribution</span><strong>{money(model.equity)}</strong><small>Estimated equity funding</small></div>
          </div>
          <div className="card" style={{marginBottom:16}}>
            <h2 className="section-title">Annual financial projection</h2><p className="section-desc">Illustrative operating model · INR</p>
            <div className="table-wrap"><table><thead><tr><th>Year</th><th>Revenue</th><th>EBITDA</th><th>Debt service</th><th>DSCR</th><th>Cash after debt</th></tr></thead><tbody>{model.rows.map(r=><tr key={r.year}><td>Year {r.year}</td><td>{money(r.revenue)}</td><td className={r.ebitda>=0?"positive":"negative"}>{money(r.ebitda)}</td><td>{money(r.debtService)}</td><td>{r.dscr===null?"—":r.dscr.toFixed(2)+"x"}</td><td className={r.cash>=0?"positive":"negative"}>{money(r.cash)}</td></tr>)}</tbody></table></div>
            <div className="note">DSCR = EBITDA ÷ scheduled principal and interest. This simplified version excludes tax, depreciation, working capital, detailed monthly amortisation and sector-specific assumptions.</div>
          </div>
          <div className="card">
            <h2 className="section-title">Revenue outlook</h2><p className="section-desc">Projected annual revenue based on the growth assumption.</p>
            {model.rows.map(r=><div className="barrow" key={r.year}><span>Year {r.year}</span><div className="bartrack"><div className="barfill" style={{width: Math.max(0, Math.min(100, r.revenue / Math.max(1,...model.rows.map(x=>x.revenue)) * 100))+"%"}}/></div><span className="barvalue">{money(r.revenue)}</span></div>)}
          </div>
        </section>
      </div>
      {exportStatus && <p className="section-desc" role="status" aria-live="polite">{exportStatus}</p>}
      <p className="footer">KaamKitPro Finance · Early staging build · Not a bank-approved DPR or lending recommendation.</p>
    </main>
  );
}
