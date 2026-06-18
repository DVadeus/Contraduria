import { Link } from "react-router-dom";
import { FileQuestion } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface Props {
  title?: string;
  description?: string;
}

export function NotFoundState({
  title = "Página no encontrada",
  description = "La página que buscas no existe o ha sido movida.",
}: Props) {
  return (
    <div className="flex items-center justify-center min-h-[60vh] p-6">
      <Card className="text-center max-w-md">
        <FileQuestion className="w-12 h-12 text-text-muted mx-auto mb-4" />
        <h2 className="font-heading text-xl text-text mb-2">{title}</h2>
        <p className="text-text-muted text-sm mb-6">{description}</p>
        <Link to="/">
          <Button>Volver al Dashboard</Button>
        </Link>
      </Card>
    </div>
  );
}