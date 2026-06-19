import { http, HttpResponse } from "msw";
import { statsFixture } from "../fixtures/stats.fixture";
import { contractsFixture } from "../fixtures/contracts.fixture";
import { contractDetailFixture } from "../fixtures/contract-detail.fixture";
import { entitiesFixture } from "../fixtures/entities.fixture";
import { suppliersFixture } from "../fixtures/suppliers.fixture";

const BASE = "/api";

export const handlers = [
  // Stats
  http.get(`${BASE}/stats`, () => HttpResponse.json(statsFixture)),

  // Analytics KPI
  http.get(`${BASE}/analytics/kpi`, () =>
    HttpResponse.json({
      total_contratos: 12847,
      valor_total: 87_300_000_000_000,
      promedio_contrato: 6_790_000_000,
      contratistas_unicos: 8923,
      entidades: 1245,
      localidades: 20,
    }),
  ),

  // Top contractors
  http.get(`${BASE}/analytics/top-contractors`, () =>
    HttpResponse.json({
      items: [
        { proveedor: "Consorcio Metro Bogotá 2032", contratos: 47, valor_total: 12_000_000_000 },
        { proveedor: "Metro Rail International Group", contratos: 12, valor_total: 9_500_000_000 },
        { proveedor: "Constructora Infraestructura Global", contratos: 89, valor_total: 8_500_000_000 },
        { proveedor: "Ingeniería Metropolitana S.A.", contratos: 156, valor_total: 7_200_000_000 },
        { proveedor: "Tecnología Militar Corp", contratos: 23, valor_total: 6_800_000_000 },
      ],
    }),
  ),

  // By locality
  http.get(`${BASE}/analytics/by-locality`, () =>
    HttpResponse.json({
      items: [
        { localidad: "Bogotá D.C.", contratos: 4500, valor_total: 35_000_000_000_000, contratistas: 4000, entidades: 200 },
        { localidad: "Medellín", contratos: 2100, valor_total: 18_000_000_000_000, contratistas: 1800, entidades: 150 },
        { localidad: "Cali", contratos: 1200, valor_total: 9_000_000_000_000, contratistas: 1000, entidades: 100 },
      ],
    }),
  ),

  // Risk contracts
  http.get(`${BASE}/analytics/risk-contracts`, () =>
    HttpResponse.json({
      items: [
        {
          id_contrato: "LP-EMB-002-2026",
          proveedor: "Consorcio Metro Bogotá 2032",
          valor_contrato: 11_250_000_000,
          contratos_proveedor: 47,
          tipo_riesgo: "concentracion",
          descripcion: "Alta concentración de contratos",
        },
        {
          id_contrato: "LP-MIN-234-2024",
          proveedor: "Metro Rail International Group",
          valor_contrato: 8_750_000_000,
          contratos_proveedor: 12,
          tipo_riesgo: "valor_atipico",
          descripcion: "Valor atípico para el sector",
        },
      ],
    }),
  ),

  // Contracts list
  http.get(`${BASE}/contratos`, () =>
    HttpResponse.json({
      items: contractsFixture,
      total: 12847,
      page: 1,
      page_size: 50,
      pages: 257,
    }),
  ),

  // Contract detail
  http.get(`${BASE}/contratos/:id`, ({ params }) => {
    if (params.id === "not-found") {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json(contractDetailFixture);
  }),

  // Entities list
  http.get(`${BASE}/entidades`, () =>
    HttpResponse.json({
      items: entitiesFixture,
      total: 1245,
      page: 1,
      page_size: 50,
      pages: 25,
    }),
  ),

  // Entity detail (by NIT)
  http.get(`${BASE}/entidades/:nit`, ({ params }) => {
    if (params.nit === "not-found") {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json({
      nit_entidad: params.nit as string,
      nombre_entidad: "Empresa Metro de Bogotá",
      contratos: 47,
      valor_total: 32_500_000_000,
      valor_pagado: 22_750_000_000,
      modalidades: [
        { modalidad: "Licitación Pública", count: 30, valor: 25_000_000_000 },
        { modalidad: "Contratación Directa", count: 17, valor: 7_500_000_000 },
      ],
      top_proveedores: [
        { proveedor: "Consorcio Metro Bogotá 2032", contratos: 20, valor: 15_000_000_000 },
      ],
    });
  }),

  // Suppliers list
  http.get(`${BASE}/proveedores`, () =>
    HttpResponse.json({
      items: suppliersFixture,
      total: 8923,
      page: 1,
      page_size: 50,
      pages: 179,
    }),
  ),

  // Server error simulation
  http.get(`${BASE}/error-test`, () =>
    new HttpResponse(JSON.stringify({ detail: "Internal Server Error" }), { status: 500 }),
  ),
];