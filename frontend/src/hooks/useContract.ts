import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useContract(id: string | undefined) {
  return useQuery({
    queryKey: ["contract", id],
    queryFn: () => api.contract(id!),
    enabled: !!id,
    staleTime: 10 * 60 * 1000,
  });
}