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

type CostKey = "Outsourcing" | "Warehouse setup" | "Hospital setup / expansion" | "Retail / pharmacy setup or expansion" | "Optical setup or expansion" | "Equipment and technology" | "Licences, deposits and professional fees" | "Initial inventory and working capital" | "Other project costs";
type ItemizedCosts = Record<CostKey, number>;
const MAX_PROJECT_COST = 1_000_000_000_000_000;
const costLabels: CostKey[] = ["Outsourcing", "Warehouse setup", "Hospital setup / expansion", "Retail / pharmacy setup or expansion", "Optical setup or expansion", "Equipment and technology", "Licences, deposits and professional fees", "Initial inventory and working capital", "Other project costs"];
const initialCosts: ItemizedCosts = {
  "Outsourcing": 1500000,
  "Warehouse setup": 2000000,
  "Hospital setup / expansion": 0,
  "Retail / pharmacy setup or expansion": 0,
  "Optical setup or expansion": 0,
  "Equipment and technology": 0,
  "Licences, deposits and professional fees": 0,
  "Initial inventory and working capital": 0,
  "Other project costs": 0,
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
  const [useItemizedCosts, setUseItemizedCosts] = useState(false);
  const [itemizedCosts, setItemizedCosts] = useState<ItemizedCosts>(initialCosts);
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
          const draft = parsed as Partial<Inputs> & { useItemizedCosts?: boolean; itemizedCosts?: Partial<ItemizedCosts> };
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
            if (typeof draft.useItemizedCosts === "boolean") setUseItemizedCosts(draft.useItemizedCosts);
            if (draft.itemizedCosts && typeof draft.itemizedCosts === "object") {
              const restored = { ...initialCosts };
              for (const key of costLabels) {
                const value = draft.itemizedCosts[key];
                if (typeof value === "number" && Number.isFinite(value) && value >= 0) restored[key] = value;
              }
              setItemizedCosts(restored);
            }
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

  const inputErrors: string[] = [];
  if (!Number.isFinite(inputs.projectCost) || inputs.projectCost < 0 || inputs.projectCost > MAX_PROJECT_COST) inputErrors.push('Project cost must be between ₹0 and ₹1,000,000,000,000,000.');
  if (!Number.isFinite(inputs.debtPct) || inputs.debtPct < 0 || inputs.debtPct > 100) inputErrors.push('Loan funding must be between 0% and 100%.');
  if (!Number.isFinite(inputs.monthlyRevenue) || inputs.monthlyRevenue < 0 || inputs.monthlyRevenue > MAX_PROJECT_COST) inputErrors.push('Monthly revenue must be a valid non-negative amount.');
  if (!Number.isFinite(inputs.growthPct) || inputs.growthPct < -100 || inputs.growthPct > 500) inputErrors.push('Annual revenue growth must be between -100% and 500%.');
  if (!Number.isFinite(inputs.variableCostPct) || inputs.variableCostPct < 0 || inputs.variableCostPct > 100) inputErrors.push('Variable costs must be between 0% and 100%.');
  if (!Number.isFinite(inputs.monthlyFixedCost) || inputs.monthlyFixedCost < 0 || inputs.monthlyFixedCost > MAX_PROJECT_COST) inputErrors.push('Monthly fixed costs must be a valid non-negative amount.');
  if (!Number.isFinite(inputs.interestPct) || inputs.interestPct < 0 || inputs.interestPct > 100) inputErrors.push('Annual interest rate must be between 0% and 100%.');
  if (!Number.isInteger(inputs.loanYears) || inputs.loanYears < 1 || inputs.loanYears > 30) inputErrors.push('Loan tenure must be a whole number from 1 to 30 years.');
  if (!Number.isInteger(inputs.projectionYears) || inputs.projectionYears < 1 || inputs.projectionYears > 100) inputErrors.push('Projection period must be a whole number from 1 to 100 years.');
  const inputError = inputErrors[0] ?? '';
  const itemizedTotal = costLabels.reduce((sum, key) => sum + itemizedCosts[key], 0);
  const itemizedCostsValid = costLabels.every((key) => Number.isFinite(itemizedCosts[key]) && itemizedCosts[key] >= 0) && Number.isFinite(itemizedTotal) && itemizedTotal <= MAX_PROJECT_COST;
  const itemizedCostsError = useItemizedCosts && !itemizedCostsValid
    ? `Itemized project costs must have a finite total of no more than ${money(MAX_PROJECT_COST)}. Reduce one or more categories before exporting.`
    : "";
  const exportsDisabled = exporting !== null || Boolean(itemizedCostsError) || Boolean(inputError);
  const effectiveProjectCost = useItemizedCosts ? (itemizedCostsValid ? itemizedTotal : 0) : inputs.projectCost;

  const model = useMemo(() => {
    const debt = effectiveProjectCost * inputs.debtPct / 100;
    const equity = effectiveProjectCost - debt;
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
  }, [inputs, effectiveProjectCost]);

  const exportCsv = () => {
    if (inputError || itemizedCostsError) { setExportStatus(inputError || itemizedCostsError); return; }
    const headers = ["Year","Revenue","Variable Cost","Fixed Cost","EBITDA","Interest","Principal","Debt Service","DSCR","Break-even Revenue","Cash After Debt Service (Pre-Tax, Pre-Capex)"];
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
    if (inputError || itemizedCostsError) { setExportStatus(inputError || itemizedCostsError); return; }
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
      project_cost: effectiveProjectCost,
      ...(useItemizedCosts ? { itemized_costs: itemizedCosts } : {}),
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
      localStorage.setItem("kaamkitpro-finance-draft", JSON.stringify({ ...inputs, useItemizedCosts, itemizedCosts }));
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
        <div className="actions"><button className="secondary" onClick={saveAssumptions}>Save draft</button><button className="secondary" onClick={exportCsv} disabled={Boolean(itemizedCostsError)}>Export CSV</button><button className="secondary" onClick={() => void exportReport("excel")} disabled={exportsDisabled}>{exporting === "excel" ? "Preparing Excel…" : "Export Excel"}</button><button className="secondary" onClick={() => void exportReport("pdf")} disabled={exportsDisabled}>{exporting === "pdf" ? "Preparing PDF…" : "Export PDF"}</button></div>
      </section>

      <div className="grid">
        <section className="card">
          <h2 className="section-title">Project assumptions</h2><p className="section-desc">Change any input to recalculate the projection instantly. Figures are in Indian rupees. Drafts stay in this browser.</p>
          {inputError && <p className="section-desc" role="alert" style={{color:"#b42318",marginBottom:12}}>{inputError}</p>}
          <div className="fields">
            <div className="field full"><label htmlFor="projectName">Project name</label><input id="projectName" value={inputs.projectName} onChange={(e) => update("projectName", e.target.value)} maxLength={120}/></div>
            <div className="field full"><label htmlFor="projectType">Business type</label><select id="projectType" value={inputs.projectType} onChange={(e) => update("projectType", e.target.value)}>{["Hospital","Pharmacy","Optical","Retail","Warehouse","Manufacturing","Services","Other"].map(x=><option key={x}>{x}</option>)}</select></div>
            <div className="field"><label htmlFor="projectCost">Total project cost (₹)</label><div className="input-wrap"><span>₹</span><input id="projectCost" type="number" min="0" value={inputs.projectCost} onChange={(e) => update("projectCost", e.target.value)}/></div></div>
            <div className="field full"><label><input type="checkbox" checked={useItemizedCosts} onChange={(e) => { setUseItemizedCosts(e.target.checked); setSaved(false); }} /> Use itemized project costs</label><p className="section-desc">Enter setup costs by category. The total will automatically replace the aggregate project cost for projections and Excel/PDF exports.</p></div>
            {useItemizedCosts && <div className="field full"><div className="table-wrap"><table><thead><tr><th>Project cost category</th><th>Amount (₹)</th></tr></thead><tbody>{costLabels.map((key) => <tr key={key}><td>{key}</td><td><input aria-label={key} type="number" min="0" max={MAX_PROJECT_COST} value={itemizedCosts[key]} onChange={(e) => { const value = Math.min(MAX_PROJECT_COST, Math.max(0, Number(e.target.value) || 0)); setItemizedCosts((prev) => ({ ...prev, [key]: value })); setSaved(false); }} /></td></tr>)}</tbody><tfoot><tr><th>Total itemized project cost</th><th>{money(itemizedTotal)}</th></tr></tfoot></table></div>{itemizedCostsError && <p className="section-desc" role="alert" style={{color:"#b42318",marginTop:10}}>{itemizedCostsError}</p>}</div>}
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
            <div className="stat blue"><span>Total project cost</span><strong>{money(effectiveProjectCost)}</strong><small>{useItemizedCosts ? "Total of itemized cost categories" : "Initial project investment"}</small></div>
            <div className="stat"><span>Estimated loan</span><strong>{money(model.debt)}</strong><small>{inputs.debtPct}% of project cost</small></div>
            <div className="stat green"><span>Owner contribution</span><strong>{money(model.equity)}</strong><small>Estimated equity funding</small></div>
          </div>
          <div className="card" style={{marginBottom:16}}>
            <h2 className="section-title">Annual financial projection</h2><p className="section-desc">Illustrative operating model · INR</p>
            <div className="table-wrap"><table><thead><tr><th>Year</th><th>Revenue</th><th>EBITDA</th><th>Debt service</th><th>DSCR</th><th>Cash after debt (pre-tax, pre-capex)</th></tr></thead><tbody>{model.rows.map(r=><tr key={r.year}><td>Year {r.year}</td><td>{money(r.revenue)}</td><td className={r.ebitda>=0?"positive":"negative"}>{money(r.ebitda)}</td><td>{money(r.debtService)}</td><td>{r.dscr===null?"—":r.dscr.toFixed(2)+"x"}</td><td className={r.cash>=0?"positive":"negative"}>{money(r.cash)}</td></tr>)}</tbody></table></div>
            <div className="note">DSCR = EBITDA ÷ scheduled principal and interest. Cash after debt service = EBITDA less interest and principal; it is pre-tax and pre-capex, not free cash flow.</div>
            <div className="note" style={{marginTop:12}}>
              <strong>Model methodology &amp; limitations</strong>
              <ul style={{margin:"8px 0 0",paddingLeft:20}}>
                <li>Year 1 revenue is monthly revenue × 12; later years compound the annual growth assumption.</li>
                <li>Variable costs move with revenue. Monthly fixed costs are annualised and held flat; inflation is not modelled.</li>
                <li>Debt is repaid using equal annual principal during the loan tenure. Interest is calculated on each year's opening loan balance; this is not a monthly EMI schedule.</li>
                <li>EBITDA is before interest, depreciation and tax. DSCR compares EBITDA with scheduled principal plus interest.</li>
                <li>The model does not yet forecast tax, depreciation, capex, working capital movements, inventory, monthly seasonality, or sector-specific operating drivers.</li>
              </ul>
              <p style={{margin:"8px 0 0"}}>Treat outputs as planning estimates. Validate assumptions and financing terms with your accountant and lender before relying on them for investment or credit decisions.</p>
            </div>
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
