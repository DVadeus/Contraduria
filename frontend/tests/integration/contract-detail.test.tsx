import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import ContractDetailPage from "@/app/contract-detail";
import { createTestQueryClient } from "../utils/createTestQueryClient";

function renderContractDetail(id = "LP-EMB-002-2026") {
  const qc = createTestQueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/contratos/${id}`]}>
        <Routes>
          <Route path="/contratos/:id" element={<ContractDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ContractDetail", () => {
  it("renders contract info", async () => {
    renderContractDetail();
    expect(await screen.findByText("LP-EMB-002-2026")).toBeInTheDocument();
    expect(screen.getByText("Empresa Metro de Bogotá")).toBeInTheDocument();
  });

  it("renders indicators panel", async () => {
    renderContractDetail();
    expect(await screen.findByText("Información General")).toBeInTheDocument();
    expect(screen.getAllByText("Ejecución Financiera").length).toBeGreaterThanOrEqual(1);
  });

  it("renders context section", async () => {
    renderContractDetail();
    expect(await screen.findByText("Contexto")).toBeInTheDocument();
  });
});