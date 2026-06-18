import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useKPI() {
  return useQuery({
    queryKey: ["kpi"],
    queryFn: api.kpi,
    staleTime: 5 * 60 * 1000,
  });
}