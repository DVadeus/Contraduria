import { useState } from "react";
import { Search } from "lucide-react";
import { Card, KpiCard } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useEntities } from "@/hooks";
import { formatCOP } from "@/lib/utils";

const MOCK_ENTITIES = [
  { nombre_entidad: "Empresa Metro de Bogotá", nit_entidad: "900.123.456", contratos: 47, valor_total: 32500000000 },
  { nombre_entidad: "IDU Bogotá", nit_entidad: "899.999.001", contratos: 312, valor_total: 18000000000 },
  { nombre_entidad: "Secretaría de Educación", nit_entidad: "800.200.300", contratos: 1203, valor_total: 9500000000 },
  { nombre_entidad: "Ministerio de Defensa", nit_entidad: "800.600.700", contratos: 89, valor_total: 15000000000 },
  { nombre_entidad: "Ministerio de Transporte", nit_entidad: "800.300.400", contratos: 234, valor_total: 28000000000 },
  { nombre_entidad: "Secretaría de Salud", nit_entidad: "900.400.500", contratos: 567, valor_total: 4200000000 },
];

export default function EntitiesPage() {
  const [search, setSearch] = useState<string | undefined>();
  const { data, isLoading } = useEntities(search);

  const entities = data?.items?.length ? data.items : MOCK_ENTITIES;

  return (
    <div className="p-6 flex flex-col gap-6">
      <div>
        <h2 className="font-heading text-3xl text-primary">Entidades Contratantes</h2>
        <p className="text-text-muted mt-1">Análisis por entidad del Estado colombiano.</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Total Entidades" value="1,245" sub="Contratantes activas" />
        <KpiCard label="Contratos Promedio" value="10.3" sub="Por entidad" />
        <KpiCard label="Valor Promedio" value="$ 2.1B" sub="Por entidad" />
        <KpiCard label="Ejecución Promedio" value="72%" sub="Valor pagado vs contratado" />
      </div>

      <div className="flex items-center gap-4">
        <div className="relative w-full max-w-md">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input
            placeholder="Buscar por nombre o NIT..."
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
              <th className="py-3 px-4 font-bold">Entidad</th>
              <th className="py-3 px-4 font-bold">NIT</th>
              <th className="py-3 px-4 font-bold">Contratos</th>
              <th className="py-3 px-4 font-bold">Valor Total</th>
              <th className="py-3 px-4 font-bold">% Ejecución</th>
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
              : entities.map((e) => (
                  <tr key={e.nit_entidad} className="hover:bg-bg cursor-pointer">
                    <td className="py-2.5 px-4 font-medium">{e.nombre_entidad}</td>
                    <td className="py-2.5 px-4 text-text-muted">{e.nit_entidad}</td>
                    <td className="py-2.5 px-4">{e.contratos}</td>
                    <td className="py-2.5 px-4 font-bold">{formatCOP(e.valor_total)}</td>
                    <td className="py-2.5 px-4">—</td>
                  </tr>
                ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}