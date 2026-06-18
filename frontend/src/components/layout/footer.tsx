export function Footer() {
  return (
    <footer className="mt-auto p-6 border-t border-muted flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-text-muted">
      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded bg-primary flex items-center justify-center">
          <span className="font-logo text-white text-[7px]">GV</span>
        </div>
        <span className="font-heading text-xs">Contraduría</span>
      </div>
      <p>© 2026 Contraduría — Datos de SECOP II. Todos los derechos reservados.</p>
    </footer>
  );
}