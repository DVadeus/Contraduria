import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useEntity(nit: string | undefined) {
  return useQuery({
    queryKey: ["entity", nit],
    queryFn: () => api.entity(nit!),
    enabled: !!nit,
    staleTime: 10 * 60 * 1000,
  });
}