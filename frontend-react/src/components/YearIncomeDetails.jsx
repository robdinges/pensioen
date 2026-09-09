const bronnen = [
  ["Arbeidsinkomen · bruto", "jaar_arbeid"],
  ["AOW · bruto", "jaar_aow"],
  ["Pensioen · bruto", "jaar_pen"],
  ["Overige inkomsten · bruto", "jaar_overig"],
  ["Arbeidsinkomen · netto ingevoerd", "jaar_arbeid_netto"],
  ["Overige inkomsten · netto ingevoerd", "jaar_overig_netto"],
];

export default function YearIncomeDetails({ jaar, jaren = [], euro }) {
  const detail = jaren.find(item => String(item.jaar) === String(jaar))?.accountant_detail;
  const bedrag = waarde => waarde == null ? "Niet beschikbaar" : euro(waarde);
  if (!detail) return <p className="notice">Inkomensdetails voor {jaar} zijn niet beschikbaar. Bereken je plan opnieuw.</p>;
  return <details className="income-year-detail">
    <summary>Waar komt je inkomen in {jaar} vandaan?</summary>
    <p>Jaarbedragen per persoon. Bruto en netto ingevoerde inkomsten staan apart. Gezamenlijke bedragen vind je in de aansluiting hieronder.</p>
    <div className="table-wrap"><table>
      <caption>Inkomensbronnen · {jaar}</caption>
      <thead><tr><th scope="col">Inkomensbron</th><th scope="col">Persoon 1</th>{detail.heeft_partner ? <th scope="col">Persoon 2</th> : null}</tr></thead>
      <tbody>{bronnen.map(([label, sleutel]) => <tr key={sleutel}>
        <th scope="row">{label}</th><td>{bedrag(detail[`${sleutel}_p1`])}</td>{detail.heeft_partner ? <td>{bedrag(detail[`${sleutel}_p2`])}</td> : null}
      </tr>)}</tbody>
    </table></div>
    <h4>Van bruto naar netto inkomen</h4>
    <p>Inclusief rendement en overige inhoudingen. Netto inkomen is nog niet wat je na alle uitgaven overhoudt; dat zie je bij vrije cashflow.</p>
    {detail.netto_aansluiting?.length ? <div className="table-wrap"><table>
      <caption>Aansluiting netto inkomen · {jaar}</caption>
      <thead><tr><th scope="col">Onderdeel</th><th scope="col">Persoon 1</th>{detail.heeft_partner ? <th scope="col">Persoon 2</th> : null}<th scope="col">Gezamenlijk / niet toegewezen</th><th scope="col">Huishouden</th></tr></thead>
      <tbody>{detail.netto_aansluiting.map((rij, index) => <tr key={`${index}-${rij.label}`}>
        <th scope="row">{rij.label}</th><td>{bedrag(rij.p1)}</td>{detail.heeft_partner ? <td>{bedrag(rij.p2)}</td> : null}<td>{bedrag(rij.gezamenlijk)}</td><td>{bedrag(rij.huishouden)}</td>
      </tr>)}</tbody>
    </table></div> : <p className="notice">De aansluiting naar netto inkomen is niet beschikbaar. Bereken je plan opnieuw.</p>}
  </details>;
}
