import { SearchX } from "lucide-react";
import { Card } from "@/components/ui/card";

interface Props {
  title?: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({
  title = "Sin resultados",
  description = "No se encontraron datos con los filtros actuales.",
  action,
}: Props) {
  return (
    <Card className="text-center py-12">
      <SearchX className="w-12 h-12 text-text-muted mx-auto mb-4" />
      <p className="text-text font-bold mb-1">{title}</p>
      <p className="text-text-muted text-sm max-w-sm mx-auto mb-4">
        {description}
      </p>
      {action}
    </Card>
  );
}