import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ContractFilters } from "@/types";

export function useContracts(filters: ContractFilters) {
  return useQuery({
    queryKey: ["contracts", filters],
    queryFn: () => api.contracts(filters),
    staleTime: 2 * 60 * 1000,
  });
}