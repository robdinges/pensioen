export default function AppShell({ sidebar, topbar, children, footer, className = "" }) {
  return (
    <div className={`layout ${className}`.trim()}>
      {sidebar}
      <main className="page">
        {topbar}
        {children}
        {footer}
      </main>
    </div>
  );
}
