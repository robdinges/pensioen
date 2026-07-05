export default function AppShell({ sidebar, topbar, children, footer }) {
  return (
    <div className="layout">
      {sidebar}
      <main className="page">
        {topbar}
        {children}
        {footer}
      </main>
    </div>
  );
}
