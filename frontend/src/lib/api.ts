import type {
  ContractDetail,
  ContractFilters,
  EntityDetail,
  EntitySummary,
  KPIResponse,
  LocalityResponse,
  PaginatedResponse,
  RiskResponse,
  StatsResponse,
  SupplierSummary,
  TopContractorsResponse,
} from "@/types";

const API_BASE = "/api";

async function fetchJSON<T>(url: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const searchParams = new URLSearchParams();
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "" && value !== null) {
        searchParams.set(key, String(value));
      }
    }
  }
  const query = searchParams.toString();
  const fullUrl = query ? `${API_BASE}${url}?${query}` : `${API_BASE}${url}`;
  const res = await fetch(fullUrl);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message || err.detail || `Error ${res.status}`);
  }
  return res.json();
}

export const api = {
  stats: () => fetchJSON<StatsResponse>("/stats"),

  kpi: () => fetchJSON<KPIResponse>("/analytics/kpi"),

  topContractors: (limit = 20) =>
    fetchJSON<TopContractorsResponse>("/analytics/top-contractors", { limit }),

  byLocality: () => fetchJSON<LocalityResponse>("/analytics/by-locality"),

  riskContracts: (threshold?: number, outlierMult?: number) =>
    fetchJSON<RiskResponse>("/analytics/risk-contracts", {
      threshold_contractor: threshold,
      outlier_multiplier: outlierMult,
    }),

  contracts: (filters: ContractFilters) =>
    fetchJSON<PaginatedResponse<ContractDetail>>("/contratos", {
      ...filters,
      page: filters.page ?? 1,
      page_size: filters.page_size ?? 50,
    }),

  contract: (id: string) => fetchJSON<ContractDetail>(`/contratos/${id}`),

  entities: (search?: string, page = 1) =>
    fetchJSON<PaginatedResponse<EntitySummary>>("/entidades", { search, page }),

  entity: (nit: string) => fetchJSON<EntityDetail>(`/entidades/${nit}`),

  suppliers: (search?: string, page = 1) =>
    fetchJSON<PaginatedResponse<SupplierSummary>>("/proveedores", { search, page }),
};