import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useRiskContracts() {
  return useQuery({
    queryKey: ["riskContracts"],
    queryFn: () => api.riskContracts(),
    staleTime: 5 * 60 * 1000,
  });
}