import { useState } from "react";
import { Search } from "lucide-react";
import { Card, KpiCard } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useSuppliers } from "@/hooks";
import { formatCOP } from "@/lib/utils";

const MOCK_SUPPLIERS = [
  { proveedor: "Consorcio Metro Bogotá 2032", documento: "901.111.222", contratos: 47, valor_total: 12000000000 },
  { proveedor: "Constructora Infraestructura Global", documento: "900.222.333", contratos: 89, valor_total: 8500000000 },
  { proveedor: "Ingeniería Metropolitana S.A.", documento: "900.333.444", contratos: 156, valor_total: 7200000000 },
  { proveedor: "Metro Rail International Group", documento: "900.444.555", contratos: 12, valor_total: 9500000000 },
  { proveedor: "Farmacéutica Nacional Ltda", documento: "900.555.666", contratos: 234, valor_total: 3100000000 },
];

const riesgoVariant = (contratos: number): "danger" | "warning" | "success" => {
  if (contratos > 100) return "danger";
  if (contratos > 50) return "warning";
  return "success";
};

const riesgoLabel = (contratos: number): string => {
  if (contratos > 100) return "Alto";
  if (contratos > 50) return "Medio";
  return "Bajo";
};

export default function SuppliersPage() {
  const [search, setSearch] = useState<string | undefined>();
  const { data, isLoading } = useSuppliers(search);

  const suppliers = data?.items?.length ? data.items : MOCK_SUPPLIERS;

  return (
    <div className="p-6 flex flex-col gap-6">
      <div>
        <h2 className="font-heading text-3xl text-primary">Proveedores</h2>
        <p className="text-text-muted mt-1">Ranking y análisis de contratistas.</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Total Proveedores" value="8,923" sub="Registrados" />
        <KpiCard label="Contratos Promedio" value="1.4" sub="Por proveedor" />
        <KpiCard label="Son PyME" value="18%" sub="Del total" />
        <KpiCard label="Concentración Alta" value="3.2%" sub="Más de 50 contratos" />
      </div>

      <div className="flex items-center gap-4">
        <div className="relative w-full max-w-md">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input
            placeholder="Buscar por nombre o documento..."
            className="pl-8"
            value={search ?? ""}
            onChange={(e) => setSearch(e.target.value || undefined)}
          />
        </div>
      </div>

      <Card className="overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-text-muted text-xs border-b border-muted">
              <th className="py-3 px-4 font-bold">Proveedor</th>
              <th className="py-3 px-4 font-bold">Documento</th>
              <th className="py-3 px-4 font-bold">Contratos</th>
              <th className="py-3 px-4 font-bold">Valor Total</th>
              <th className="py-3 px-4 font-bold">Riesgo Concentración</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-muted">
            {isLoading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 5 }).map((_, j) => (
                      <td key={j} className="py-2.5 px-4"><Skeleton className="h-4 w-full" /></td>
                    ))}
                  </tr>
                ))
              : suppliers.map((s) => (
                  <tr key={s.proveedor} className="hover:bg-bg cursor-pointer">
                    <td className="py-2.5 px-4 font-medium">{s.proveedor}</td>
                    <td className="py-2.5 px-4 text-text-muted">{s.documento || "—"}</td>
                    <td className="py-2.5 px-4">{s.contratos}</td>
                    <td className="py-2.5 px-4 font-bold">{formatCOP(s.valor_total)}</td>
                    <td className="py-2.5 px-4">
                      <Badge variant={riesgoVariant(s.contratos)}>
                        {riesgoLabel(s.contratos)}
                      </Badge>
                    </td>
                  </tr>
                ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}