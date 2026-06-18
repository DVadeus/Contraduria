import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useSuppliers(search?: string, page = 1) {
  return useQuery({
    queryKey: ["suppliers", search, page],
    queryFn: () => api.suppliers(search, page),
    staleTime: 5 * 60 * 1000,
  });
}