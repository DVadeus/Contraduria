import { useState, useEffect, useCallback } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Search, SlidersHorizontal, ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useContracts } from "@/hooks";
import { formatCOP, formatDate } from "@/lib/utils";
import type { ContractFilters } from "@/types";

const MOCK_CONTRACTS = [
  { id_contrato: "LP-EMB-002-2026", nombre_entidad: "Empresa Metro de Bogotá", proveedor_adjudicado: "Consorcio Metro Bogotá 2032", valor_contrato: 11250000000, fecha_firma: "2026-03-15", estado_contrato: "En ejecución", modalidad_contratacion: "Licitación Pública" },
  { id_contrato: "CD-IDU-045-2025", nombre_entidad: "IDU Bogotá", proveedor_adjudicado: "Constructora Infraestructura Global", valor_contrato: 3200000000, fecha_firma: "2025-08-01", estado_contrato: "En ejecución", modalidad_contratacion: "Contratación Directa" },
  { id_contrato: "SA-SEC-112-2026", nombre_entidad: "Secretaría de Educación", proveedor_adjudicado: "Alimentos Escolares S.A.", valor_contrato: 5800000000, fecha_firma: "2026-01-10", estado_contrato: "En ejecución", modalidad_contratacion: "Selección Abreviada" },
  { id_contrato: "MC-FON-089-2025", nombre_entidad: "Fondo Nacional de Regalías", proveedor_adjudicado: "Ingeniería Metropolitana S.A.", valor_contrato: 150000000, fecha_firma: "2025-11-20", estado_contrato: "Finalizado", modalidad_contratacion: "Mínima Cuantía" },
  { id_contrato: "LP-MIN-234-2024", nombre_entidad: "Ministerio de Transporte", proveedor_adjudicado: "Metro Rail International", valor_contrato: 8750000000, fecha_firma: "2024-06-01", estado_contrato: "En ejecución", modalidad_contratacion: "Licitación Pública" },
];

const MODALIDADES = ["Licitación Pública", "Contratación Directa", "Selección Abreviada", "Mínima Cuantía"];
const ANIOS = [2026, 2025, 2024, 2023, 2022, 2021, 2020];

const estadoVariant = (estado: string | null): "success" | "warning" | "default" => {
  if (!estado) return "default";
  if (estado.toLowerCase().includes("ejecución") || estado.toLowerCase().includes("activo")) return "success";
  if (estado.toLowerCase().includes("suspendido")) return "warning";
  return "default";
};

function filtersFromParams(params: URLSearchParams): ContractFilters {
  const f: ContractFilters = { page: 1, page_size: 50 };
  const anio = params.get("anio");
  if (anio) f.anio = Number(anio);
  const entidad = params.get("entidad");
  if (entidad) f.entidad = entidad;
  const proveedor = params.get("proveedor");
  if (proveedor) f.proveedor = proveedor;
  const modalidad = params.get("modalidad");
  if (modalidad) f.modalidad = modalidad;
  const page = params.get("page");
  if (page) f.page = Number(page);
  const valor_min = params.get("valor_min");
  if (valor_min) f.valor_min = Number(valor_min);
  const valor_max = params.get("valor_max");
  if (valor_max) f.valor_max = Number(valor_max);
  return f;
}

function paramsFromFilters(f: ContractFilters): URLSearchParams {
  const p = new URLSearchParams();
  if (f.anio != null) p.set("anio", String(f.anio));
  if (f.entidad) p.set("entidad", f.entidad);
  if (f.proveedor) p.set("proveedor", f.proveedor);
  if (f.modalidad) p.set("modalidad", f.modalidad);
  if (f.page && f.page > 1) p.set("page", String(f.page));
  if (f.valor_min != null) p.set("valor_min", String(f.valor_min));
  if (f.valor_max != null) p.set("valor_max", String(f.valor_max));
  return p;
}

export default function ContractsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialFilters = filtersFromParams(searchParams);
  const [filters, setFilters] = useState<ContractFilters>(initialFilters);
  const [showFilters, setShowFilters] = useState(false);
  const { data, isLoading } = useContracts(filters);

  // Sync filters → URL (one-way: state → query params)
  useEffect(() => {
    const newParams = paramsFromFilters(filters);
    const currentStr = searchParams.toString();
    const newStr = newParams.toString();
    if (currentStr !== newStr) {
      setSearchParams(newParams, { replace: true });
    }
  }, [filters, setSearchParams, searchParams]);

  const contracts = data?.items?.length ? data.items : MOCK_CONTRACTS;
  const total = data?.total ?? 12847;

  return (
    <div className="p-6 flex flex-col gap-6">
      <div>
        <h2 className="font-heading text-3xl text-primary">Contratos</h2>
        <p className="text-text-muted mt-1">Explora y filtra los contratos públicos de Colombia.</p>
      </div>

      <div className="grid lg:grid-cols-[280px_1fr] gap-6">
        <motion.aside
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          className={showFilters ? "block" : "hidden lg:block"}
        >
          <Card className="flex flex-col gap-5 sticky top-[4.5rem]">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-sm">Filtros</h4>
              <button
                className="text-xs text-text-muted hover:text-text"
                onClick={() => setFilters({ page: 1, page_size: 50 })}
              >
                Reiniciar
              </button>
            </div>
            <div>
              <label className="text-xs font-bold text-text-muted">Año</label>
              <select
                className="w-full mt-1 px-3 py-2 rounded-lg border border-muted bg-bg text-sm"
                value={filters.anio ?? ""}
                onChange={(e) => setFilters((f) => ({ ...f, anio: e.target.value ? Number(e.target.value) : undefined, page: 1 }))}
              >
                <option value="">Todos</option>
                {ANIOS.map((y) => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-bold text-text-muted">Entidad</label>
              <Input
                placeholder="Nombre o NIT"
                value={filters.entidad ?? ""}
                onChange={(e) => setFilters((f) => ({ ...f, entidad: e.target.value || undefined, page: 1 }))}
              />
            </div>
            <div>
              <label className="text-xs font-bold text-text-muted">Proveedor</label>
              <Input
                placeholder="Nombre o documento"
                value={filters.proveedor ?? ""}
                onChange={(e) => setFilters((f) => ({ ...f, proveedor: e.target.value || undefined, page: 1 }))}
              />
            </div>
            <div>
              <label className="text-xs font-bold text-text-muted">Modalidad</label>
              <select
                className="w-full mt-1 px-3 py-2 rounded-lg border border-muted bg-bg text-sm"
                value={filters.modalidad ?? ""}
                onChange={(e) => setFilters((f) => ({ ...f, modalidad: e.target.value || undefined, page: 1 }))}
              >
                <option value="">Todas</option>
                {MODALIDADES.map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-bold text-text-muted">Rango de Valor (COP)</label>
              <div className="flex gap-2 mt-1">
                <Input
                  type="number"
                  placeholder="Mín"
                  value={filters.valor_min ?? ""}
                  onChange={(e) => setFilters((f) => ({ ...f, valor_min: e.target.value ? Number(e.target.value) : undefined, page: 1 }))}
                />
                <Input
                  type="number"
                  placeholder="Máx"
                  value={filters.valor_max ?? ""}
                  onChange={(e) => setFilters((f) => ({ ...f, valor_max: e.target.value ? Number(e.target.value) : undefined, page: 1 }))}
                />
              </div>
            </div>
          </Card>
        </motion.aside>

        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-4">
            <p className="text-sm text-text-muted">
              Mostrando {contracts.length} de {total.toLocaleString()} contratos
            </p>
            <div className="flex items-center gap-2">
              <div className="relative w-56">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <Input
                  placeholder="Buscar por ID, objeto..."
                  className="pl-8"
                  value={filters.entidad ?? ""}
                  onChange={(e) => setFilters((f) => ({ ...f, entidad: e.target.value || undefined, page: 1 }))}
                />
              </div>
              <Button variant="outline" size="icon" className="lg:hidden" onClick={() => setShowFilters(!showFilters)}>
                <SlidersHorizontal className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <Card className="overflow-x-auto p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-text-muted text-xs border-b border-muted">
                  <th className="py-3 px-4 font-bold">ID Contrato</th>
                  <th className="py-3 px-4 font-bold">Entidad</th>
                  <th className="py-3 px-4 font-bold">Proveedor</th>
                  <th className="py-3 px-4 font-bold">Valor</th>
                  <th className="py-3 px-4 font-bold">Fecha</th>
                  <th className="py-3 px-4 font-bold">Estado</th>
                  <th className="py-3 px-4 font-bold">Modalidad</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-muted">
                {isLoading
                  ? Array.from({ length: 5 }).map((_, i) => (
                      <tr key={i}>
                        {Array.from({ length: 7 }).map((_, j) => (
                          <td key={j} className="py-2.5 px-4"><Skeleton className="h-4 w-full" /></td>
                        ))}
                      </tr>
                    ))
                  : contracts.map((c) => (
                      <tr key={c.id_contrato} className="hover:bg-bg cursor-pointer">
                        <td className="py-2.5 px-4 text-primary font-medium">{c.id_contrato}</td>
                        <td className="py-2.5 px-4">{c.nombre_entidad || "—"}</td>
                        <td className="py-2.5 px-4">{c.proveedor_adjudicado || "—"}</td>
                        <td className="py-2.5 px-4 font-bold">{formatCOP(c.valor_contrato)}</td>
                        <td className="py-2.5 px-4 text-text-muted">{formatDate(c.fecha_firma)}</td>
                        <td className="py-2.5 px-4">
                          <Badge variant={estadoVariant(c.estado_contrato)}>{c.estado_contrato || "—"}</Badge>
                        </td>
                        <td className="py-2.5 px-4 text-text-muted">{c.modalidad_contratacion || "—"}</td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </Card>

          <div className="flex items-center justify-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={filters.page === 1}
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) - 1 }))}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-sm text-text-muted">
              Página {filters.page ?? 1} de {Math.ceil(total / (filters.page_size ?? 50))}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) + 1 }))}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}