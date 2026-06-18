import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useEntities(search?: string, page = 1) {
  return useQuery({
    queryKey: ["entities", search, page],
    queryFn: () => api.entities(search, page),
    staleTime: 5 * 60 * 1000,
  });
}