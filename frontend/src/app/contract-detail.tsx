import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, ExternalLink, Building2, User, Calendar, DollarSign, FileText, AlertTriangle, TrendingUp, CheckCircle } from "lucide-react";
import { Card, KpiCard } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useContract } from "@/hooks";
import { formatCOP, formatDate, formatPercent } from "@/lib/utils";

const estadoVariant = (estado: string | null): "success" | "warning" | "default" => {
  if (!estado) return "default";
  const e = estado.toLowerCase();
  if (e.includes("ejecución") || e.includes("activo")) return "success";
  if (e.includes("suspendido")) return "warning";
  if (e.includes("finalizado") || e.includes("liquidado")) return "default";
  return "default";
};

export default function ContractDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: contract, isLoading, error } = useContract(id);

  if (isLoading) return <ContractDetailSkeleton />;

  const c = contract;

  const valorAlto =
    c?.valor_contrato != null && c?.valor_contrato > 5_000_000_000;

  const ejecucionPct =
    c?.valor_contrato && c?.valor_pagado
      ? Math.round((c.valor_pagado / c.valor_contrato) * 100)
      : null;

  return (
    <div className="p-6 flex flex-col gap-8 max-w-5xl">
      {/* Back + Title */}
      <div className="flex flex-col gap-2">
        <Link
          to="/contratos"
          className="flex items-center gap-1 text-sm text-text-muted hover:text-text w-fit"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver a contratos
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="font-heading text-3xl text-primary">
              {c?.id_contrato ?? `Contrato ${id}`}
            </h2>
            {c?.objeto_contrato && (
              <p className="text-text-muted mt-1 line-clamp-2">
                {c.objeto_contrato}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {c?.estado_contrato && (
              <Badge variant={estadoVariant(c.estado_contrato)}>
                {c.estado_contrato}
              </Badge>
            )}
            {c?.url_proceso && (
              <a
                href={c.url_proceso}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-sm text-secondary hover:underline"
              >
                <ExternalLink className="w-4 h-4" />
                SECOP
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Investigator Indicators */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card
            className={
              valorAlto
                ? "border-danger/30 bg-red-50 dark:bg-red-950/20"
                : "border-muted"
            }
          >
            <div className="flex items-center gap-2 mb-2">
              {valorAlto ? (
                <AlertTriangle className="w-5 h-5 text-danger" />
              ) : (
                <DollarSign className="w-5 h-5 text-text-muted" />
              )}
              <p className="text-sm font-bold text-text">
                {valorAlto ? "Valor Alto" : "Valor del Contrato"}
              </p>
            </div>
            <p className="font-heading text-2xl text-primary">
              {formatCOP(c?.valor_contrato)}
            </p>
            {valorAlto && (
              <p className="text-xs text-danger mt-1">
                Supera el umbral de $5B COP
              </p>
            )}
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <Card className="border-muted">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-text-muted" />
              <p className="text-sm font-bold text-text">Ejecución Financiera</p>
            </div>
            <p className="font-heading text-2xl text-primary">
              {ejecucionPct != null ? `${ejecucionPct}%` : "—"}
            </p>
            <p className="text-xs text-text-muted mt-1">
              Pagado: {formatCOP(c?.valor_pagado)} / Contratado:{" "}
              {formatCOP(c?.valor_contrato)}
            </p>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="border-muted">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-5 h-5 text-text-muted" />
              <p className="text-sm font-bold text-text">Modalidad</p>
            </div>
            <p className="font-heading text-lg text-primary">
              {c?.modalidad_contratacion || "—"}
            </p>
            {c?.tipo_contrato && (
              <p className="text-xs text-text-muted mt-1">
                Tipo: {c.tipo_contrato}
              </p>
            )}
          </Card>
        </motion.div>
      </div>

      {/* Main Info Grid */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
      >
        <Card>
          <h3 className="font-heading text-lg text-primary mb-6">
            Información General
          </h3>
          <div className="grid sm:grid-cols-2 gap-x-12 gap-y-5">
            <InfoRow icon={Building2} label="Entidad" value={c?.nombre_entidad} />
            <InfoRow icon={User} label="Proveedor" value={c?.proveedor_adjudicado} />
            <InfoRow icon={Calendar} label="Fecha de firma" value={formatDate(c?.fecha_firma)} />
            <InfoRow icon={Calendar} label="Fecha de inicio" value={formatDate(c?.fecha_inicio)} />
            <InfoRow icon={Calendar} label="Fecha de fin" value={formatDate(c?.fecha_fin)} />
            <InfoRow icon={DollarSign} label="Valor facturado" value={formatCOP(c?.valor_facturado)} />
            <InfoRow label="NIT Entidad" value={c?.nit_entidad} />
            <InfoRow label="Documento Proveedor" value={c?.documento_proveedor} />
            <InfoRow label="Departamento" value={c?.departamento} />
            <InfoRow label="Ciudad" value={c?.ciudad} />
            <InfoRow label="Localización" value={c?.localizacion} />
            <InfoRow label="Duración" value={c?.duracion_contrato} />
            <InfoRow label="Días adicionados" value={c?.dias_adicionados != null ? String(c.dias_adicionados) : null} />
            <InfoRow label="Sector" value={c?.sector} />
            <InfoRow label="Rama" value={c?.rama} />
            <InfoRow label="Origen de recursos" value={c?.origen_recursos} />
            <InfoRow label="Destino del gasto" value={c?.destino_gasto} />
            <InfoRow label="Posconflicto" value={c?.es_postconflicto} />
          </div>
        </Card>
      </motion.div>

      {/* Object */}
      {c?.objeto_contrato && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <h3 className="font-heading text-lg text-primary mb-4">
              Objeto del Contrato
            </h3>
            <p className="text-text text-sm leading-relaxed whitespace-pre-line">
              {c.objeto_contrato}
            </p>
          </Card>
        </motion.div>
      )}

      {/* Execution Progress */}
      {c?.valor_contrato != null && c?.valor_pagado != null && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
        >
          <Card>
            <h3 className="font-heading text-lg text-primary mb-4">
              Ejecución Financiera
            </h3>
            <div className="flex flex-col gap-3">
              <div className="flex justify-between text-sm">
                <span className="text-text-muted">Contratado</span>
                <span className="font-bold">{formatCOP(c.valor_contrato)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-text-muted">Pagado</span>
                <span className="font-bold">{formatCOP(c.valor_pagado)}</span>
              </div>
              <div className="w-full h-3 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full rounded-full bg-success transition-all duration-1000"
                  style={{
                    width: `${Math.min(ejecucionPct ?? 0, 100)}%`,
                  }}
                />
              </div>
              <p className="text-xs text-text-muted text-right">
                {ejecucionPct}% ejecutado
              </p>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Context Links */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card>
          <h3 className="font-heading text-lg text-primary mb-4">Contexto</h3>
          <div className="flex flex-wrap gap-3">
            {c?.nit_entidad && (
              <Link to={`/entidades`}>
                <Button variant="outline" size="sm">
                  <Building2 className="w-4 h-4" />
                  Otros contratos de {c.nombre_entidad}
                </Button>
              </Link>
            )}
            {c?.documento_proveedor && (
              <Link to={`/proveedores`}>
                <Button variant="outline" size="sm">
                  <User className="w-4 h-4" />
                  Otros contratos de {c.proveedor_adjudicado}
                </Button>
              </Link>
            )}
            {c?.url_proceso && (
              <a href={c.url_proceso} target="_blank" rel="noopener noreferrer">
                <Button variant="outline" size="sm">
                  <ExternalLink className="w-4 h-4" />
                  Ver en SECOP II
                </Button>
              </a>
            )}
          </div>
        </Card>
      </motion.div>
    </div>
  );
}

function InfoRow({
  icon: Icon,
  label,
  value,
}: {
  icon?: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | null | undefined;
}) {
  return (
    <div className="flex items-start gap-2">
      {Icon && <Icon className="w-4 h-4 text-text-muted mt-0.5 shrink-0" />}
      <div className="min-w-0">
        <p className="text-xs text-text-muted font-bold">{label}</p>
        <p className="text-sm text-text mt-0.5 truncate">{value || "—"}</p>
      </div>
    </div>
  );
}

function ContractDetailSkeleton() {
  return (
    <div className="p-6 flex flex-col gap-8 max-w-5xl">
      <div className="flex flex-col gap-2">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-8 w-96" />
        <Skeleton className="h-5 w-72" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <Skeleton className="h-4 w-24 mb-2" />
            <Skeleton className="h-8 w-36" />
            <Skeleton className="h-3 w-20 mt-1" />
          </Card>
        ))}
      </div>
      <Card>
        <Skeleton className="h-6 w-48 mb-6" />
        <div className="grid sm:grid-cols-2 gap-x-12 gap-y-5">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i}>
              <Skeleton className="h-3 w-20 mb-1" />
              <Skeleton className="h-4 w-40" />
            </div>
          ))}
        </div>
      </Card>
      <Card>
        <Skeleton className="h-6 w-40 mb-4" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4 mt-2" />
        <Skeleton className="h-4 w-1/2 mt-2" />
      </Card>
    </div>
  );
}