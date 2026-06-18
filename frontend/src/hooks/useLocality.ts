import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useLocality() {
  return useQuery({
    queryKey: ["locality"],
    queryFn: api.byLocality,
    staleTime: 5 * 60 * 1000,
  });
}