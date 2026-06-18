import { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navbar } from "@/components/layout/navbar";
import { Sidebar } from "@/components/layout/sidebar";
import { Footer } from "@/components/layout/footer";
import { useTheme } from "@/hooks/useTheme";
import { NotFoundState } from "@/components/error/NotFoundState";
import { AppErrorBoundary } from "@/components/error/AppErrorBoundary";
import { Skeleton } from "@/components/ui/skeleton";

const DashboardPage = lazy(() => import("./dashboard"));
const ContractsPage = lazy(() => import("./contracts"));
const ContractDetailPage = lazy(() => import("./contract-detail"));
const EntitiesPage = lazy(() => import("./entities"));
const SuppliersPage = lazy(() => import("./suppliers"));

function PageSkeleton() {
  return (
    <div className="p-6 flex flex-col gap-8 max-w-5xl">
      <Skeleton className="h-8 w-64" />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-2xl border border-muted p-6">
            <Skeleton className="h-4 w-24 mb-2" />
            <Skeleton className="h-8 w-32" />
          </div>
        ))}
      </div>
      <div className="grid lg:grid-cols-2 gap-6">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="rounded-2xl border border-muted p-6">
            <Skeleton className="h-6 w-48 mb-4" />
            <Skeleton className="h-72 w-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

function AppContent() {
  const { isDark, toggle } = useTheme();

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar isDark={isDark} onToggleTheme={toggle} />
      <div className="flex flex-1">
        <Sidebar isDark={isDark} onToggleTheme={toggle} />
        <main className="flex-1 flex flex-col min-w-0">
          <div className="flex-1">
            <AppErrorBoundary>
              <Suspense fallback={<PageSkeleton />}>
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/contratos" element={<ContractsPage />} />
                  <Route path="/contratos/:id" element={<ContractDetailPage />} />
                  <Route path="/entidades" element={<EntitiesPage />} />
                  <Route path="/proveedores" element={<SuppliersPage />} />
                  <Route path="*" element={<NotFoundState />} />
                </Routes>
              </Suspense>
            </AppErrorBoundary>
          </div>
          <Footer />
        </main>
      </div>
    </div>
  );
}