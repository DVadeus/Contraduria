import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface Props {
  message?: string;
  onRetry: () => void;
  retrying?: boolean;
}

export function RetryState({
  message = "Algo salió mal al cargar estos datos.",
  onRetry,
  retrying,
}: Props) {
  return (
    <Card className="text-center py-8">
      <RefreshCw
        className={`w-10 h-10 text-text-muted mx-auto mb-3 ${
          retrying ? "animate-spin" : ""
        }`}
      />
      <p className="text-text-muted text-sm mb-4">{message}</p>
      <Button variant="outline" onClick={onRetry} disabled={retrying}>
        <RefreshCw className="w-4 h-4" />
        {retrying ? "Reintentando..." : "Reintentar"}
      </Button>
    </Card>
  );
}