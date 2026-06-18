import { Link, useLocation } from "react-router-dom";
import { Search, Sun, Moon, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { KeyboardEvent } from "react";

const NAV_LINKS = [
  { to: "/", label: "Dashboard" },
  { to: "/contratos", label: "Contratos" },
  { to: "/entidades", label: "Entidades" },
  { to: "/proveedores", label: "Proveedores" },
];

interface NavbarProps {
  isDark: boolean;
  onToggleTheme: () => void;
}

export function Navbar({ isDark, onToggleTheme }: NavbarProps) {
  const { pathname } = useLocation();

  const handleSearchKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      const value = (e.target as HTMLInputElement).value;
      if (value.trim()) {
        window.location.href = `/contratos?search=${encodeURIComponent(value.trim())}`;
      } else {
        window.location.href = "/contratos";
      }
    }
  };

  return (
    <header className="flex items-center justify-between h-14 px-6 border-b border-muted bg-surface sticky top-0 z-50">
      <div className="flex items-center gap-4">
        <Link to="/" className="flex items-center gap-2 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
            <span className="font-logo text-white text-[9px] leading-none">
              GV
            </span>
          </div>
          <span className="font-heading text-lg text-primary hidden sm:inline">
            Contraduría
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-1 ml-8">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={cn(
                "px-3 py-1.5 rounded-lg text-sm transition-colors",
                pathname === link.to
                  ? "bg-muted text-text font-bold"
                  : "text-text-muted hover:bg-muted hover:text-text"
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative hidden md:block">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input
            placeholder="Buscar contratos..."
            className="pl-8 w-56 h-9 text-sm"
            onKeyDown={handleSearchKeyDown}
          />
        </div>

        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleTheme}
          aria-label={isDark ? "Modo claro" : "Modo oscuro"}
        >
          {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </Button>
      </div>
    </header>
  );
}