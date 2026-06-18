import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class AppErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[AppErrorBoundary]", error, info.componentStack);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex items-center justify-center min-h-[60vh] p-6">
          <Card className="max-w-md text-center">
            <AlertTriangle className="w-12 h-12 text-danger mx-auto mb-4" />
            <h2 className="font-heading text-xl text-text mb-2">
              Algo salió mal
            </h2>
            <p className="text-text-muted text-sm mb-4">
              Ha ocurrido un error inesperado. Intenta recargar la página.
            </p>
            <div className="flex flex-col gap-2">
              <Button onClick={this.handleRetry}>
                <RefreshCw className="w-4 h-4" />
                Reintentar
              </Button>
              <Button
                variant="outline"
                onClick={() => window.location.reload()}
              >
                Recargar página
              </Button>
            </div>
            {this.state.error && (
              <details className="mt-4 text-left">
                <summary className="text-xs text-text-muted cursor-pointer">
                  Detalles técnicos
                </summary>
                <pre className="mt-2 text-xs text-danger bg-bg p-3 rounded-lg overflow-auto max-h-40">
                  {this.state.error.message}
                </pre>
              </details>
            )}
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}