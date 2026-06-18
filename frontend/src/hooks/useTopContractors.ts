import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useTopContractors(limit = 20) {
  return useQuery({
    queryKey: ["topContractors", limit],
    queryFn: () => api.topContractors(limit),
    staleTime: 5 * 60 * 1000,
  });
}