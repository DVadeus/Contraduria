import { RefreshCw, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface Props {
  message?: string;
  onRetry?: () => void;
}

export function ApiErrorState({
  message = "Error al cargar los datos. Verifica tu conexión e inténtalo de nuevo.",
  onRetry,
}: Props) {
  return (
    <Card className="text-center py-12">
      <AlertCircle className="w-12 h-12 text-danger mx-auto mb-4" />
      <p className="text-text font-bold mb-2">Error de conexión</p>
      <p className="text-text-muted text-sm max-w-md mx-auto mb-4">
        {message}
      </p>
      {onRetry && (
        <Button variant="outline" onClick={onRetry}>
          <RefreshCw className="w-4 h-4" />
          Reintentar
        </Button>
      )}
    </Card>
  );
}