export default function AccountantSection({ SectionHeader, resultsSection }) {
  return (
    <>
      <section className="section">
        <SectionHeader title="Accountant" description="Deze stap wordt in volgende implementatiefase uitgebreid met detailniveau zoals de Streamlit pagina." />
        <p>Huidige basis toont jaarresultaten als startpunt.</p>
      </section>
      {resultsSection}
    </>
  );
}