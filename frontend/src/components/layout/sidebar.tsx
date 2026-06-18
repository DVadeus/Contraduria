import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, FileText, Building2, Users, Sun, Moon } from "lucide-react";
import { cn } from "@/lib/utils";

const SIDEBAR_LINKS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/contratos", label: "Contratos", icon: FileText },
  { to: "/entidades", label: "Entidades", icon: Building2 },
  { to: "/proveedores", label: "Proveedores", icon: Users },
];

interface SidebarProps {
  isDark: boolean;
  onToggleTheme: () => void;
}

export function Sidebar({ isDark, onToggleTheme }: SidebarProps) {
  const { pathname } = useLocation();

  return (
    <aside className="hidden md:flex flex-col items-center py-6 px-2 border-r border-muted bg-surface w-16 shrink-0 sticky top-14 h-[calc(100vh-3.5rem)]">
      <nav className="flex flex-col gap-2 flex-1 pt-4">
        {SIDEBAR_LINKS.map((link) => {
          const Icon = link.icon;
          const isActive = pathname === link.to;
          return (
            <Link
              key={link.to}
              to={link.to}
              className={cn(
                "w-11 h-11 flex items-center justify-center rounded-xl transition-colors",
                isActive
                  ? "bg-primary text-white"
                  : "text-text-muted hover:bg-muted"
              )}
              title={link.label}
            >
              <Icon className="w-5 h-5" />
            </Link>
          );
        })}
      </nav>

      <button
        onClick={onToggleTheme}
        className="w-11 h-11 flex items-center justify-center rounded-xl text-text-muted hover:bg-muted transition-colors"
        aria-label={isDark ? "Modo claro" : "Modo oscuro"}
      >
        {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
      </button>
    </aside>
  );
}