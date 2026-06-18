# Design Analysis — Contraduría

## Fuente

Archivo Figma: `VztJun9mdgFDRyAr05VYKn` ("Gato Veedor")

---

## Design Tokens Extraídos

### Color Palette

| Token | Hex | Uso |
|-------|-----|-----|
| Fondo/Azul | `#00274A` | Fondos oscuros, navbar, headings |
| Fondo/Cyan | `#39A9DB` | Acentos, botones CTA |
| Fondo/Blanco | `#F8F9FF` | Fondo principal |
| Fondo/Nieve | `#F6F6F6` | Superficies secundarias |
| Fondo/Gris | `#DFE0E5` | Bordes, separadores |
| Fondo/Amarillo | `#EEC139` | Toggle activo, destacados |
| Texto/Body | `#05051C` | Texto principal |
| Texto/Gris oscuro | `#58585A` | Texto secundario, captions |
| Dark mode / Dark Grey | `#36373B` | Barra inferior móvil dark |
| Secondary | `#FFFFFF` | Texto sobre fondos oscuros |

### Typography Scale

| Nivel | Font Family | Weight | Size | Line Height |
|-------|-------------|--------|------|-------------|
| H1 | Libre Baskerville | Bold 700 | 96px | 132px |
| H2 | Libre Baskerville | Bold 700 | 64px | 80px |
| H3 | Quattrocento Sans | Bold 700 | 32px | 38px |
| H4 | Quattrocento Sans | Bold 700 | 28px | 34px |
| H5 | Quattrocento Sans | Bold 700 | 24px | 30px |
| S1 | Quattrocento Sans | Regular 400 | 20px | 28px |
| S2 | Quattrocento Sans | Bold 700 | 20px | 28px |
| S3 | Quattrocento Sans | Regular 400 | 15px | 24px |
| S4 | Quattrocento Sans | Bold 700 | 16px | 22px |
| B1 | Quattrocento Sans | Regular 400 | 16px | 24px |
| B2 | Quattrocento Sans | Bold 700 | 16px | 24px |
| B3 | Quattrocento Sans | Regular 400 | 14px | 20px |
| B4 | Quattrocento Sans | Bold 700 | 14px | 20px |
| C1 | Quattrocento Sans | Regular 400 | 12px | 16px |
| C2 | Quattrocento Sans | Bold 700 | 12px | 16px |
| Logo | Afacad | Regular 400 | 12px | 12px |

### Spacing & Layout

- **Desktop width:** 1440px
- **Mobile width:** 440px
- **Sidebar width:** 80px (desktop)
- **Card radius:** 16px (cards), 24px (casos), 8px (botones), 12px (menú)
- **Grid gaps:** 8px, 16px, 24px, 40px, 48px
- **Section padding:** 24px, 48px, 72px, 144px

---

## Component Inventory

### Navegación
- **Bottom menu / Dark mode** (448:1982): Barra inferior móvil con 5 iconos
- **Bottom menu / Light mode** (448:1854): Variante clara
- **Menu / Desktop** (182:293): Sidebar vertical con iconos (Inicio, Estrella, Buscar, Info)
- **Menu / Mobile** (312:1509): Barra inferior horizontal con 4 iconos

### Botones
- **Botón / Azul** (209:381): Primary CTA, padding 16px/24px, border-radius 8px
- **Botón / Blanco** (369:1124): Secondary, con borde gris
- **Boton menu** (129:186): Icono 48×48, estados Main/Hover/Selected
- **Boton Filtro** (125:150): Tamaños Big/Small, estados Main/Selected/Hover

### Cards
- **Caso** (152:136): Card destacada con imagen de fondo, gradiente overlay, texto blanco
- **Contrato** (250:524): Card con imagen, categorías, título, ubicación, descripción, valor
- **Hito** (245:1593): Timeline con check, título y fecha

### Filtros
- **Info** (249:501): Badge de categoría (Outline/Filled)
- **Toggle** (268:1031): Switch para filtros binarios
- **Location** (152:134): Badge de ubicación con icono
- **Buscar** (312:1215): Input de búsqueda con icono

### Data Display
- **Cronograma** (417:1050): Timeline vertical con hitos y conectores
- **Carousel** (335:829): Carrusel vertical de casos destacados
- **Logo** (327:734): Variantes Portrait, Isotipo, Landscape

### Iconos (34 iconos vectoriales)
Ambiente, Casas, Gafas, Camión, Fuego, Edificio, Industria, Marrano, Rural, Buscar, Estrella, Home, Info, Libro, Hospital, Radio, Tren, Chincheta, Iglesia, Maletín, Patineta, Árbol, Radioactivo, Tienda, Cine, Bodega, Dinero, Moto, Bicicleta, Vía, Clima, TV, Sofá, Banco, Papeles, Basket, Consola, Periódico, Mercado, PC, Tarjetas, Filtro, Cancel

---

## Pantallas Identificadas

### Desktop (1440×1080)
1. **Home** — Hero con cita + carrusel vertical de casos + logo
2. **Featured** — Grid 2×2 de casos destacados con imágenes
3. **Search** — Panel de filtros (categoría, ubicación, tipo) + grid de resultados
4. **Caso** — Detalle completo: fotos, descripción, información general, cronograma, mapa, contratos similares
5. **Nosotros** — Perfil del concejal, especialidades, descripción

### Mobile (440×956)
1. **Home M** — Hero con cita + carrusel
2. **Featured M** — Scroll vertical de casos con bottom menu
3. **Search M** — Búsqueda + resultados verticales con filtros en modal
4. **Caso M** — Detalle scrollable con bottom menu
5. **Nosotros M** — Perfil con bottom menu

---

## UX Observations

### Fortalezas
1. **Branding fuerte:** El gato veedor es un símbolo memorable y diferenciador
2. **Tipografía con personalidad:** Libre Baskerville para headlines da seriedad institucional
3. **Paleta de color institucional:** Azul profundo transmite confianza gubernamental
4. **Mobile-first coherente:** La experiencia móvil está bien pensada
5. **Componentes reutilizables:** Sistema de diseño consistente con estados bien definidos
6. **Imágenes de alto impacto:** Las cards usan fotos con gradientes que generan interés visual
7. **Timeline visual:** El cronograma con hitos es claro e informativo

### Debilidades
1. **Sin visualización de datos:** No hay gráficos, tablas ni métricas numéricas
2. **Navegación limitada:** Solo 4 secciones accesibles desde el menú
3. **Falta de búsqueda avanzada:** Los filtros no incluyen rangos de valor ni fechas
4. **Sin datos de ejecución financiera:** No se muestra % de avance ni pagos
5. **Sin indicadores de riesgo:** No hay alertas de concentración o valores atípicos
6. **Accesibilidad limitada:** Sin skip links, roles ARIA incompletos
7. **Sin dark mode completo:** Solo la barra inferior tiene variante dark

### Oportunidades de Mejora
1. **Dashboard analítico:** KPIs + charts (barras, pie, líneas) usando Recharts
2. **Tabla de contratos:** Con sort, filtros avanzados y paginación
3. **Indicadores de riesgo:** Alertas de concentración de contratistas y valores atípicos
4. **Ejecución financiera:** Barras de progreso, comparación contratado vs pagado
5. **Mapa de localidades:** React Leaflet con datos agregados por localidad
6. **Dark mode completo:** Toggle en navbar
7. **Cmd+K search:** Búsqueda rápida estilo Linear/Superset
8. **Análisis por entidad/proveedor:** Vistas dedicadas con agregados

---

## Design Principles Extraídos

1. **Transparencia como valor central** — El diseño comunica apertura y acceso público
2. **Jerarquía tipográfica clara** — H1-H5 con pesos y tamaños bien definidos
3. **Economía de color** — Paleta reducida (4 colores principales + grises)
4. **Mobile-first** — Todas las pantallas tienen versión móvil
5. **Componentes con estados** — Cada componente tiene Main, Hover, Selected/Active
6. **Imágenes como narrativa** — Las fotos contextualizan los contratos
7. **Iconografía consistente** — 34 iconos vectoriales con mismo estilo y peso
8. **Espaciado generoso** — Padding amplio para respiración visual