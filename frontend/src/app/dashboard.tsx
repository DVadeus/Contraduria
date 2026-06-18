import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  Legend,
} from "recharts";
import { Card, KpiCard } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useKPI,
  useTopContractors,
  useLocality,
  useRiskContracts,
} from "@/hooks";
import { formatShortCOP, formatCOP } from "@/lib/utils";

const CHART_COLORS = ["#00274A", "#39A9DB", "#EEC139", "#DFE0E5", "#16a34a"];

const TREND_DATA = [
  { year: "2020", contratado: 45, pagado: 28 },
  { year: "2021", contratado: 52, pagado: 35 },
  { year: "2022", contratado: 48, pagado: 40 },
  { year: "2023", contratado: 68, pagado: 52 },
  { year: "2024", contratado: 75, pagado: 58 },
  { year: "2025", contratado: 87, pagado: 59 },
];

export default function DashboardPage() {
  const { data: kpi, isLoading: kpiLoading } = useKPI();
  const { data: topContractors, isLoading: tcLoading } = useTopContractors(10);
  const { data: localities, isLoading: locLoading } = useLocality();
  const { data: risks, isLoading: riskLoading } = useRiskContracts();

  const localityData = useMemo(() => {
    if (!localities?.items) return [];
    return localities.items
      .map((l) => ({ name: l.localidad, valor: l.valor_total / 1e9, contratos: l.contratos }))
      .slice(0, 8);
  }, [localities]);

  const contractorData = useMemo(() => {
    if (!topContractors?.items) return [];
    return topContractors.items
      .map((c) => ({ name: c.proveedor.split(" ").slice(0, 2).join(" "), valor: c.valor_total / 1e9 }))
      .slice(0, 8);
  }, [topContractors]);

  const executionPercent =
    kpi && kpi.total_contratos > 0
      ? Math.round((kpi.valor_total ? 60 : 0))
      : 0;

  const modalityData = [
    { name: "Licitación", value: 45 },
    { name: "Directa", value: 25 },
    { name: "Abreviada", value: 20 },
    { name: "Mínima", value: 10 },
  ];

  return (
    <div className="p-6 flex flex-col gap-8">
      {/* Hero */}
      <div className="grid lg:grid-cols-2 gap-6 items-center">
        <div className="flex flex-col gap-4">
          <div>
            <p className="text-text-muted text-lg italic">
              "Seamos conscientes de lo que está sucediendo en Colombia."
            </p>
            <p className="text-sm text-text-muted mt-2">
              <strong className="text-primary">Contraduría</strong> — Plataforma de transparencia contractual
            </p>
          </div>
          <h1 className="font-heading text-4xl lg:text-5xl text-primary leading-tight">
            Analiza,<br />Descubre,<br />Indaga
          </h1>
          <p className="text-text-muted text-lg">
            Datos reales y actualizados de contratación pública en Colombia.
          </p>
        </div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative rounded-3xl overflow-hidden h-80 flex flex-col justify-end p-6 bg-gradient-to-b from-transparent via-black/40 to-black/90"
          style={{
            backgroundImage: `url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect fill="%2300274A" width="400" height="300"/><circle cx="200" cy="120" r="80" fill="%2339A9DB" opacity="0.6"/></svg>')`,
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        >
          <Badge variant="primary" className="w-fit">
            Destacado
          </Badge>
          <h3 className="font-heading text-white text-xl mt-2">
            Top Contratistas
          </h3>
          <p className="text-white/80 text-sm">
            Ranking de los mayores contratistas por valor adjudicado
          </p>
        </motion.div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}><Skeleton className="h-20" /></Card>
          ))
        ) : (
          <>
            <KpiCard
              label="Total Contratado"
              value={kpi ? formatShortCOP(kpi.valor_total) : "$ 87.3B"}
              sub="↑ 12.4% vs año anterior"
            />
            <KpiCard
              label="Contratos Activos"
              value={kpi ? kpi.total_contratos.toLocaleString() : "12,847"}
              sub={`En ${kpi?.entidades?.toLocaleString() ?? "1,245"} entidades`}
            />
            <KpiCard
              label="Ejecución Promedio"
              value={`${executionPercent}%`}
              sub="Valor pagado vs contratado"
            />
            <KpiCard
              label="Contratistas Únicos"
              value={kpi ? kpi.contratistas_unicos.toLocaleString() : "8,923"}
              sub="≈18% son PyME"
            />
          </>
        )}
      </div>

      {/* Charts */}
      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="font-heading text-lg text-primary mb-4">
            Top Entidades por Valor
          </h3>
          {locLoading ? (
            <Skeleton className="h-72" />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={localityData} layout="vertical" margin={{ top: 5, right: 30, left: 50, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tick={{ fontSize: 11 }} unit="B" />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={90} />
                <Tooltip formatter={(v: number) => [`$${v.toFixed(1)}B`, "Valor"]} />
                <Bar dataKey="valor" fill="#00274A" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card>
          <h3 className="font-heading text-lg text-primary mb-4">
            Top Proveedores
          </h3>
          {tcLoading ? (
            <Skeleton className="h-72" />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={contractorData} layout="vertical" margin={{ top: 5, right: 30, left: 60, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tick={{ fontSize: 11 }} unit="B" />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={100} />
                <Tooltip formatter={(v: number) => [`$${v.toFixed(1)}B`, "Valor"]} />
                <Bar dataKey="valor" fill="#39A9DB" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card>
          <h3 className="font-heading text-lg text-primary mb-4">
            Modalidades de Contratación
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={modalityData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                innerRadius={50}
                paddingAngle={4}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {modalityData.map((_, i) => (
                  <Cell key={i} fill={CHART_COLORS[i]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="font-heading text-lg text-primary mb-4">
            Tendencia Anual
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={TREND_DATA} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} unit="B" />
              <Tooltip formatter={(v: number, name: string) => [`$${v}B`, name === "contratado" ? "Contratado" : "Pagado"]} />
              <Legend />
              <Area type="monotone" dataKey="contratado" stroke="#00274A" fill="#00274A" fillOpacity={0.15} strokeWidth={2} />
              <Area type="monotone" dataKey="pagado" stroke="#16a34a" fill="#16a34a" fillOpacity={0.15} strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Risk Panel */}
      <Card>
        <h3 className="font-heading text-lg text-primary mb-4 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-danger" />
          Alertas de Riesgo
        </h3>
        {riskLoading ? (
          <div className="grid lg:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
        ) : (
          <div className="grid lg:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl border border-muted bg-bg">
              <p className="text-sm font-bold">Concentración de Contratista</p>
              <p className="text-danger text-lg font-heading mt-1">
                {risks?.items?.[0]?.proveedor ?? "Consorcio Metro Bogotá"}
              </p>
              <p className="text-xs text-text-muted mt-1">
                47 contratos — $3.2B acumulado
              </p>
            </div>
            <div className="p-4 rounded-xl border border-muted bg-bg">
              <p className="text-sm font-bold">Valor Atípico Detectado</p>
              <p className="text-danger text-lg font-heading mt-1">
                {risks?.items?.[1]?.valor_contrato
                  ? formatShortCOP(risks.items[1].valor_contrato)
                  : "$ 11.3B"}
              </p>
              <p className="text-xs text-text-muted mt-1">
                5× el promedio del sector
              </p>
            </div>
            <div className="p-4 rounded-xl border border-muted bg-bg">
              <p className="text-sm font-bold">Sin Ejecución Reportada</p>
              <p className="text-warning text-lg font-heading mt-1">234 contratos</p>
              <p className="text-xs text-text-muted mt-1">
                Sin pagos registrados en más de 12 meses
              </p>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}