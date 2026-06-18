export interface ContractSummary {
  id_contrato: string;
  nombre_entidad: string | null;
  proveedor_adjudicado: string | null;
  valor_contrato: number | null;
  fecha_firma: string | null;
  estado_contrato: string | null;
  modalidad_contratacion: string | null;
}

export interface ContractDetail extends ContractSummary {
  nit_entidad: string | null;
  departamento: string | null;
  ciudad: string | null;
  objeto_contrato: string | null;
  fecha_inicio: string | null;
  fecha_fin: string | null;
  valor_pagado: number | null;
  valor_facturado: number | null;
  documento_proveedor: string | null;
  url_proceso: string | null;
  tipo_contrato: string | null;
  duracion_contrato: string | null;
  dias_adicionados: number | null;
  localizacion: string | null;
  sector: string | null;
  rama: string | null;
  origen_recursos: string | null;
  destino_gasto: string | null;
  es_postconflicto: string | null;
}

export interface ContractFilters {
  anio?: number;
  entidad?: string;
  proveedor?: string;
  modalidad?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  valor_min?: number;
  valor_max?: number;
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface StatsResponse {
  total_contratos: number;
  total_entidades: number;
  total_proveedores: number;
  valor_total_contratado: number;
  valor_total_pagado: number;
  anio_desde: number;
  anio_hasta: number;
  ultima_actualizacion: string | null;
}

export interface KPIResponse {
  total_contratos: number;
  valor_total: number;
  promedio_contrato: number;
  contratistas_unicos: number;
  entidades: number;
  localidades: number;
}

export interface TopContractor {
  proveedor: string;
  contratos: number;
  valor_total: number;
}

export interface TopContractorsResponse {
  items: TopContractor[];
}

export interface LocalityItem {
  localidad: string;
  contratos: number;
  valor_total: number;
  contratistas: number;
  entidades: number;
}

export interface LocalityResponse {
  items: LocalityItem[];
}

export interface RiskContract {
  id_contrato: string;
  proveedor: string;
  valor_contrato: number;
  contratos_proveedor: number;
  tipo_riesgo: "concentracion" | "valor_atipico";
  descripcion: string;
}

export interface RiskResponse {
  items: RiskContract[];
}

export interface EntitySummary {
  nombre_entidad: string;
  nit_entidad: string;
  contratos: number;
  valor_total: number;
}

export interface EntityDetail {
  nit_entidad: string;
  nombre_entidad: string;
  contratos: number;
  valor_total: number;
  valor_pagado: number;
  modalidades: { modalidad: string; count: number; valor: number }[];
  top_proveedores: { proveedor: string; contratos: number; valor: number }[];
}

export interface SupplierSummary {
  proveedor: string;
  documento: string | null;
  contratos: number;
  valor_total: number;
}