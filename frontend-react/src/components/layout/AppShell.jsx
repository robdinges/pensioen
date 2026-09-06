export default function AppShell({ sidebar, topbar, children, footer, className = "" }) {
  return (
    <div className={`layout ${className}`.trim()}>
      <a className="skip-link" href="#plan-content">Ga naar inhoud</a>
      {sidebar}
      <main className="page" id="plan-content" tabIndex={-1}>
        {topbar}
        {children}
        {footer}
      </main>
    </div>
  );
}
