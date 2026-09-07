function number(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function percentage(value, digits = 2) {
  return `${(number(value) * 100).toFixed(digits)}%`;
}

function CalculationTable({ rows, euro, hasPartner, showShared = false }) {
  const visibleRows = rows.filter((row) => !row.optional || row.values.some((value) => number(value) !== 0));

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Berekeningsregel</th>
            <th>Persoon 1</th>
            {hasPartner ? <th>Persoon 2</th> : null}
            {showShared ? <th>Gezamenlijk / niet toegewezen</th> : null}
            <th>Huishouden</th>
          </tr>
        </thead>
        <tbody>
          {visibleRows.map((row) => {
            const p1 = number(row.values[0]);
            const p2 = number(row.values[1]);
            const total = row.total == null ? p1 + p2 : number(row.total);
            return (
              <tr key={row.label}>
                <td><strong>{row.label}</strong>{row.note ? <><br /><small>{row.note}</small></> : null}</td>
                <td>{euro(p1)}</td>
                {hasPartner ? <td>{euro(p2)}</td> : null}
                {showShared ? <td>{euro(number(row.shared))}</td> : null}
                <td><strong>{euro(total)}</strong></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function DetailNotice({ children }) {
  return <p className="notice">{children}</p>;
}

function AccountantYear({ jaarResultaat, euro }) {
  const detail = jaarResultaat?.accountant_detail || {};
  const months = Array.isArray(jaarResultaat?.maanden) ? jaarResultaat.maanden : [];
  const tarieven = months[0]?.gebruikte_tarieven || {};
  const hasPartner = Boolean(detail.heeft_partner);
  const eigenWoningP1 = detail.ew_p1 || {};
  const eigenWoningP2 = detail.ew_p2 || {};
  const heeftEigenWoning = Boolean(detail.ew_invoer_gevonden)
    || [eigenWoningP1, eigenWoningP2].some((woning) => [
      woning.eigenwoningforfait,
      woning.aftrekbare_hypotheekrente,
      woning.box1_mutatie,
      woning.tariefsaanpassing,
    ].some((value) => number(value) !== 0));

  const brutoRows = [
    { label: "Arbeidsinkomen", values: [detail.jaar_arbeid_p1, detail.jaar_arbeid_p2] },
    { label: "AOW-uitkering", values: [detail.jaar_aow_p1, detail.jaar_aow_p2] },
    { label: "Werkgeverspensioen", values: [detail.jaar_pen_p1, detail.jaar_pen_p2] },
    { label: "Overig belast inkomen", values: [detail.jaar_overig_p1, detail.jaar_overig_p2], optional: true },
    { label: "Totaal bruto inkomen", values: [detail.bruto_p1, detail.bruto_p2] },
  ];
  const woningRows = [
    { label: "Eigenwoningforfait", values: [eigenWoningP1.eigenwoningforfait, eigenWoningP2.eigenwoningforfait] },
    { label: "Af: hypotheekrente", values: [-number(eigenWoningP1.aftrekbare_hypotheekrente), -number(eigenWoningP2.aftrekbare_hypotheekrente)] },
    { label: "Af: overige aftrekbare kosten", values: [-number(eigenWoningP1.overige_aftrekbare_kosten), -number(eigenWoningP2.overige_aftrekbare_kosten)], optional: true },
    { label: "Wet Hillen-vermindering", values: [-number(eigenWoningP1.hillen_correctie), -number(eigenWoningP2.hillen_correctie)], optional: true },
    { label: "Correctie box 1-grondslag", values: [eigenWoningP1.box1_mutatie, eigenWoningP2.box1_mutatie] },
  ];
  const belastingRows = [
    { label: "Belastbaar inkomen box 1", values: [detail.box1_grondslag_p1, detail.box1_grondslag_p2] },
    { label: "Inkomstenbelasting vóór kortingen", values: [detail.bel_voor_korting_p1, detail.bel_voor_korting_p2] },
  ];
  const premieRows = [
    { label: "AOW-premie", values: [detail.premie_aow_p1, detail.premie_aow_p2], note: "Alleen verschuldigd vóór de AOW-leeftijd" },
    { label: "Anw-premie", values: [detail.premie_anw_p1, detail.premie_anw_p2] },
    { label: "Wlz-premie", values: [detail.premie_wlz_p1, detail.premie_wlz_p2] },
    { label: "Totaal premies volksverzekeringen", values: [detail.totaal_premies_p1, detail.totaal_premies_p2] },
  ];
  const kortingRows = [
    { label: "Algemene heffingskorting", values: [detail.ahk_p1, detail.ahk_p2], note: "Op basis van belastbaar inkomen en AOW-status" },
    { label: "Arbeidskorting", values: [detail.ak_p1, detail.ak_p2], note: "Op basis van arbeidsinkomen" },
    { label: "Ouderenkorting", values: [detail.ok_p1, detail.ok_p2], note: "Alleen bij AOW-status" },
    { label: "Alleenstaandeouderenkorting", values: [detail.aok_p1, detail.aok_p2], note: "Alleen bij alleenstaand en AOW-status" },
    { label: "Totaal heffingskortingen", values: [detail.totale_hk_p1, detail.totale_hk_p2] },
  ];
  const verschuldigdRows = [
    { label: "Inkomstenbelasting vóór kortingen", values: [detail.bel_voor_korting_p1, detail.bel_voor_korting_p2] },
    { label: "Premies volksverzekeringen", values: [detail.totaal_premies_p1, detail.totaal_premies_p2] },
    { label: "Tariefsaanpassing eigen woning", values: [eigenWoningP1.tariefsaanpassing, eigenWoningP2.tariefsaanpassing], optional: true },
    { label: "Berekende heffingskortingen", values: [detail.totale_hk_p1, detail.totale_hk_p2], note: "Beschikbaar volgens de kortingberekening" },
    { label: "Maximaal verrekenbaar", values: [detail.totaal_ib_en_premies_p1, detail.totaal_ib_en_premies_p2], note: "Heffingskortingen kunnen de verschuldigde IB en premies niet verder dan nul verlagen" },
    { label: "Af: daadwerkelijk verrekende heffingskortingen", values: [-number(detail.verrekende_hk_p1), -number(detail.verrekende_hk_p2)] },
    { label: "Niet-benutte heffingskortingen", values: [detail.niet_verrekende_hk_p1, detail.niet_verrekende_hk_p2], optional: true },
    { label: "Verschuldigde box 1-belasting", values: [detail.netto_bel_p1, detail.netto_bel_p2] },
  ];
  const nettoRows = (detail.netto_aansluiting || []).map((row) => ({
    label: row.label, values: [row.p1, row.p2], shared: row.gezamenlijk, total: row.huishouden,
  }));

  return (
    <div className="accountant-year-detail">
      {jaarResultaat.tarieven_aanname ? <DetailNotice>{jaarResultaat.tarieven_aanname}</DetailNotice> : null}

      <div className="kpis">
        <div className="kpi"><span>Box 1 verschuldigd</span><strong>{euro(detail.totaal_netto_belasting_box1)}</strong></div>
        <div className="kpi"><span>Netto inkomen</span><strong>{euro(detail.totaal_netto_inkomen)}</strong></div>
        <div className="kpi"><span>Box 3-heffing</span><strong>{euro(detail.box3_heffing)}</strong></div>
        <div className="kpi"><span>Vermogen einde jaar</span><strong>{euro(detail.saldo_einde_jaar)}</strong></div>
      </div>

      <h3>1. Bruto inkomen</h3>
      <CalculationTable rows={brutoRows} euro={euro} hasPartner={hasPartner} />

      {heeftEigenWoning ? <>
        <h3>2. Eigen woning: correctie op box 1</h3>
        <CalculationTable rows={woningRows} euro={euro} hasPartner={hasPartner} />
      </> : null}

      <h3>3. Belastbaar inkomen en inkomstenbelasting</h3>
      <CalculationTable rows={belastingRows} euro={euro} hasPartner={hasPartner} />
      <DetailNotice>
        AOW-breuk persoon 1: {percentage(detail.aow_breuk_p1, 1)}
        {hasPartner ? ` · persoon 2: ${percentage(detail.aow_breuk_p2, 1)}` : ""}.
        De getoonde inkomstenbelasting is exclusief premies volksverzekeringen.
      </DetailNotice>

      <h3>4. Premies volksverzekeringen</h3>
      <CalculationTable rows={premieRows} euro={euro} hasPartner={hasPartner} />

      <h3>5. Heffingskortingen</h3>
      <CalculationTable rows={kortingRows} euro={euro} hasPartner={hasPartner} />

      <h3>6. Verschuldigde box 1-belasting</h3>
      <CalculationTable rows={verschuldigdRows} euro={euro} hasPartner={hasPartner} />
      <DetailNotice>
        <strong>Nog te controleren:</strong> de engine begrenst de verrekening van heffingskortingen op de berekende inkomstenbelasting plus premies. Een eventueel restant wordt niet uitbetaald en staat hierboven als niet-benut. Controleer nog of deze begrenzing voor alle gebruikte heffingskortingen fiscaal juist is.
      </DetailNotice>

      <h3>7. Netto inkomen</h3>
      <DetailNotice>Persoon 1 + persoon 2 + gezamenlijk sluiten aan op het huishoudtotaal. Rendement en niet per persoon toegewezen inhoudingen staan apart. Huishoudelijke uitgaven en box 3 volgen bij de vrije cashflow.</DetailNotice>
      {nettoRows.length ? <CalculationTable rows={nettoRows} euro={euro} hasPartner={hasPartner} showShared /> : <DetailNotice>Bereken opnieuw om de volledige netto-opbouw te zien.</DetailNotice>}

      <h3>8. Box 3-heffing</h3>
      <div className="table-wrap">
        <table>
          <tbody>
            <tr><td>Vermogen begin jaar</td><td>{euro(detail.saldo_begin_jaar)}</td></tr>
            <tr><td>Af: vrijstelling</td><td>{euro(-number(detail.box3_vrijstelling))}</td></tr>
            <tr><td><strong>Belastbaar vermogen</strong></td><td><strong>{euro(detail.box3_belastbaar)}</strong></td></tr>
            <tr><td>Verdeling</td><td>{percentage(detail.box3_spaargeld_fractie, 1)} spaargeld / {percentage(1 - number(detail.box3_spaargeld_fractie), 1)} overig</td></tr>
            <tr><td>Forfaitair rendement</td><td>{euro(detail.box3_fictief_rendement)}</td></tr>
            <tr><td>Box 3-tarief</td><td>{percentage(detail.box3_tarief)}</td></tr>
            <tr><td><strong>Box 3-heffing</strong></td><td><strong>{euro(detail.box3_heffing)}</strong></td></tr>
          </tbody>
        </table>
      </div>
      {detail.box3_info ? <DetailNotice>{detail.box3_info}</DetailNotice> : null}

      {detail.vermogen_rijen?.length ? <details>
        <summary>Saldoverloop en bijgewerkte standen</summary>
        <p>Een correctie uit een nieuwe saldostand vervangt de berekende waarde. Dit is geen inkomen of inleg.</p>
        <div className="table-wrap"><table>
          <thead><tr><th>Maand</th><th>Beginsaldo</th><th>Cashflow incl. inleg</th><th>Correctie saldostand</th><th>Eindsaldo</th></tr></thead>
          <tbody>{detail.vermogen_rijen.map(row => <tr key={row.maand}>
            <td>{row.maand}</td><td>{euro(row.saldo_begin)}</td><td>{euro(row.netto_cashflow)}</td>
            <td>{euro(row.saldo_correctie || 0)}</td><td>{euro(row.saldo_eind)}</td>
          </tr>)}</tbody>
        </table></div>
      </details> : null}

      <details>
        <summary>Gebruikte tarieven en aannames</summary>
        <div className="table-wrap">
          <table>
            <tbody>
              <tr><td>Controlejaar</td><td>{jaarResultaat.jaar}</td></tr>
              <tr><td>Gebruikt belastingjaar</td><td>{jaarResultaat.tarieven_jaar || jaarResultaat.jaar}</td></tr>
              <tr><td>Premiegrens</td><td>{euro(tarieven.persoon1?.premies_config?.premiegrens)}</td></tr>
              <tr><td>Box 3-forfait spaargeld</td><td>{percentage(detail.box3_forfait_spaargeld)}</td></tr>
              <tr><td>Box 3-forfait overig</td><td>{percentage(detail.box3_forfait_overig)}</td></tr>
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

export default function AccountantSection({ SectionHeader, resultaat, euro }) {
  const jaren = Array.isArray(resultaat?.cashflow?.jaren) ? resultaat.cashflow.jaren : [];

  return (
    <section className="section">
      <SectionHeader
        title="Toelichting berekening"
        description="Van bruto inkomen naar belasting, netto inkomen en vermogen. Alle bedragen komen rechtstreeks uit de rekenengine."
      />
      {jaren.length === 0 ? <p>Voer eerst een berekening uit om de toelichting te tonen.</p> : jaren.map((jaarResultaat, index) => {
        const detail = jaarResultaat.accountant_detail || {};
        return (
          <details className="accountant-year section" key={jaarResultaat.jaar} defaultOpen={index === 0}>
            <summary className="accountant-year-summary">
              <span className="accountant-year-copy">
                <strong>{jaarResultaat.jaar}</strong> · box 1 {euro(detail.totaal_netto_belasting_box1)} · netto {euro(detail.totaal_netto_inkomen)} · box 3 {euro(detail.box3_heffing)}
              </span>
              <span className="chevron" aria-hidden="true">⌄</span>
            </summary>
            <AccountantYear jaarResultaat={jaarResultaat} euro={euro} />
          </details>
        );
      })}
    </section>
  );
}
