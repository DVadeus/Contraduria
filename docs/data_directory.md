# Catálogo de Datos – Contraduría

## Información General

| Atributo                    | Valor                                            |
| --------------------------- | ------------------------------------------------ |
| Proyecto                    | Contraduría                                      |
| Fuente Principal            | SECOP II                                         |
| Plataforma                  | Socrata Open Data                                |
| Dataset ID                  | jbjy-vk9h                                        |
| Endpoint                    | https://www.datos.gov.co/resource/jbjy-vk9h.json |
| Formato                     | JSON                                             |
| Frecuencia de actualización | Según publicación SECOP II                       |
| Capa origen                 | Bronze                                           |
| Responsable                 | Equipo Contraduría                               |

---

# Arquitectura de Datos

```text
SECOP II (Socrata)
        │
        ▼
     Bronze
(Datos crudos JSON)
        │
        ▼
     Silver
(Tipos normalizados,
campos limpiados)
        │
        ▼
      Gold
(Métricas,
agregaciones,
KPIs)
```

---

# Convenciones

## Tipos de Datos

| Tipo     | Descripción    |
| -------- | -------------- |
| string   | Texto corto    |
| text     | Texto largo    |
| integer  | Número entero  |
| decimal  | Número decimal |
| boolean  | Valor lógico   |
| date     | Fecha          |
| datetime | Fecha y hora   |
| url      | URL            |
| object   | Objeto JSON    |

## Niveles ETL

| Nivel  | Descripción                                   |
| ------ | --------------------------------------------- |
| Bronze | Datos originales extraídos sin transformación |
| Silver | Datos normalizados y validados                |
| Gold   | Datos agregados para análisis                 |

---


# Claves de Negocio

| Campo               | Descripción                               |
| ------------------- | ----------------------------------------- |
| id_contrato         | Identificador único del contrato          |
| proceso_de_compra   | Identificador del proceso de contratación |
| nit_entidad         | Identificador tributario de la entidad    |
| documento_proveedor | Identificador del proveedor               |
| codigo_entidad      | Código SECOP de la entidad                |
| codigo_proveedor    | Código SECOP del proveedor                |

---

# Diccionario de Datos

## Entidad Contratante

| Columna              | Tipo Origen | Nivel ETL          | Descripción                      | Uso                         |
| -------------------- | ----------- | ------------------ | -------------------------------- | --------------------------- |
| nombre_entidad       | string      | Bronze/Silver/Gold | Nombre de la entidad contratante | Agrupación institucional    |
| nit_entidad          | string      | Bronze/Silver/Gold | NIT de la entidad                | Identificación única        |
| departamento         | string      | Bronze/Silver/Gold | Departamento de la entidad       | Análisis territorial        |
| ciudad               | string      | Bronze/Silver/Gold | Municipio o ciudad               | Análisis geográfico         |
| localizaci_n         | string      | Bronze/Silver      | Ubicación textual                | Georreferenciación          |
| orden                | string      | Bronze/Silver/Gold | Nivel administrativo             | Clasificación institucional |
| sector               | string      | Bronze/Silver/Gold | Sector gubernamental             | Segmentación                |
| rama                 | string      | Bronze/Silver/Gold | Rama del poder público           | Clasificación               |
| entidad_centralizada | string      | Bronze/Silver      | Centralizada o descentralizada   | Organización institucional  |
| codigo_entidad       | string      | Bronze/Silver/Gold | Código SECOP entidad             | Integración                 |

## Proceso Contractual

| Columna                       | Tipo Origen | Nivel ETL          | Descripción               | Uso                     |
| ----------------------------- | ----------- | ------------------ | ------------------------- | ----------------------- |
| proceso_de_compra             | string      | Bronze/Silver/Gold | Código del proceso        | Trazabilidad            |
| id_contrato                   | string      | Bronze/Silver/Gold | Identificador contractual | Clave principal         |
| referencia_del_contrato       | string      | Bronze/Silver      | Referencia interna        | Auditoría               |
| estado_contrato               | string      | Bronze/Silver/Gold | Estado actual             | Seguimiento             |
| modalidad_de_contratacion     | string      | Bronze/Silver/Gold | Modalidad legal           | Análisis normativo      |
| tipo_de_contrato              | string      | Bronze/Silver/Gold | Tipo contractual          | Clasificación           |
| codigo_de_categoria_principal | string      | Bronze/Silver/Gold | Código UNSPSC             | Clasificación económica |
| descripcion_del_proceso       | text        | Bronze/Silver      | Resumen del proceso       | Búsquedas               |
| objeto_del_contrato           | text        | Bronze/Silver      | Objeto completo           | NLP y auditoría         |

## Fechas

| Columna                      | Tipo Origen | Nivel ETL          | Descripción         | Uso            |
| ---------------------------- | ----------- | ------------------ | ------------------- | -------------- |
| fecha_de_firma               | datetime    | Bronze/Silver/Gold | Fecha de firma      | Línea temporal |
| fecha_de_inicio_del_contrato | datetime    | Bronze/Silver/Gold | Inicio de ejecución | Seguimiento    |
| fecha_de_fin_del_contrato    | datetime    | Bronze/Silver/Gold | Fin previsto        | Control        |
| duraci_n_del_contrato        | string      | Bronze/Silver      | Duración textual    | Validación     |
| dias_adicionados             | integer     | Bronze/Silver/Gold | Días adicionados    | Auditoría      |

## Proveedor

| Columna              | Tipo Origen | Nivel ETL          | Descripción                 | Uso                      |
| -------------------- | ----------- | ------------------ | --------------------------- | ------------------------ |
| proveedor_adjudicado | string      | Bronze/Silver/Gold | Nombre proveedor            | Análisis de contratistas |
| documento_proveedor  | string      | Bronze/Silver      | Documento proveedor         | Identificación           |
| tipodocproveedor     | string      | Bronze/Silver      | Tipo documento              | Clasificación            |
| codigo_proveedor     | string      | Bronze/Silver/Gold | Código SECOP proveedor      | Integración              |
| es_grupo             | string      | Bronze/Silver      | Indicador grupo empresarial | Segmentación             |
| es_pyme              | string      | Bronze/Silver/Gold | Indicador PyME              | Análisis empresarial     |

## Valores Contractuales

| Columna                      | Tipo Origen | Nivel ETL          | Descripción        | Uso                    |
| ---------------------------- | ----------- | ------------------ | ------------------ | ---------------------- |
| valor_del_contrato           | string      | Bronze/Silver/Gold | Valor adjudicado   | KPI principal          |
| valor_facturado              | string      | Bronze/Silver      | Valor facturado    | Seguimiento financiero |
| valor_pagado                 | string      | Bronze/Silver/Gold | Valor pagado       | Ejecución              |
| valor_pendiente_de_pago      | string      | Bronze/Silver      | Saldo pendiente    | Seguimiento            |
| valor_pendiente_de_ejecucion | string      | Bronze/Silver      | Ejecución restante | Control                |
| saldo_cdp                    | string      | Bronze/Silver      | Saldo presupuestal | Gestión financiera     |

# Información Normativa y Contractual

| Columna                          | Tipo Origen | Nivel ETL          | Descripción                                                    | Uso                            |
| -------------------------------- | ----------- | ------------------ | -------------------------------------------------------------- | ------------------------------ |
| justificacion_modalidad_de       | string      | Bronze/Silver      | Justificación legal de la modalidad de contratación utilizada. | Auditoría normativa.           |
| condiciones_de_entrega           | text        | Bronze/Silver      | Condiciones pactadas para la entrega del bien o servicio.      | Análisis contractual.          |
| habilita_pago_adelantado         | string      | Bronze/Silver      | Indica si el contrato permite pagos anticipados.               | Riesgo financiero.             |
| liquidaci_n                      | string      | Bronze/Silver/Gold | Indica si el contrato requiere o tiene liquidación.            | Seguimiento contractual.       |
| obligaci_n_ambiental             | string      | Bronze/Silver      | Existencia de obligaciones ambientales asociadas.              | Control ambiental.             |
| obligaciones_postconsumo         | string      | Bronze/Silver      | Existencia de obligaciones postconsumo.                        | Cumplimiento normativo.        |
| reversion                        | string      | Bronze/Silver      | Indica si existe cláusula de reversión.                        | Evaluación jurídica.           |
| el_contrato_puede_ser_prorrogado | string      | Bronze/Silver      | Posibilidad de prórroga contractual.                           | Seguimiento de modificaciones. |


# Financiación y Presupuesto

| Columna                                                          | Tipo Origen | Nivel ETL          | Descripción                                                | Uso                                |
| ---------------------------------------------------------------- | ----------- | ------------------ | ---------------------------------------------------------- | ---------------------------------- |
| origen_de_los_recursos                                           | string      | Bronze/Silver/Gold | Fuente general de financiación.                            | Análisis presupuestal.             |
| destino_gasto                                                    | string      | Bronze/Silver/Gold | Clasificación del gasto (inversión, funcionamiento, etc.). | Estudios fiscales.                 |
| presupuesto_general_de_la_nacion_pgn                             | string      | Bronze/Silver/Gold | Recursos provenientes del PGN.                             | Seguimiento financiero nacional.   |
| sistema_general_de_participaciones                               | string      | Bronze/Silver/Gold | Recursos provenientes del SGP.                             | Seguimiento territorial.           |
| sistema_general_de_regal_as                                      | string      | Bronze/Silver/Gold | Recursos provenientes del SGR.                             | Control de regalías.               |
| recursos_propios_alcald_as_gobernaciones_y_resguardos_ind_genas_ | string      | Bronze/Silver/Gold | Recursos propios de entidades territoriales.               | Evaluación financiera territorial. |
| recursos_de_credito                                              | string      | Bronze/Silver/Gold | Recursos obtenidos mediante endeudamiento.                 | Seguimiento fiscal.                |
| recursos_propios                                                 | string      | Bronze/Silver/Gold | Recursos propios de la entidad contratante.                | Análisis financiero.               |

# Ejecución Financiera

| Columna                  | Tipo Origen | Nivel ETL     | Descripción                                            | Uso                     |
| ------------------------ | ----------- | ------------- | ------------------------------------------------------ | ----------------------- |
| valor_de_pago_adelantado | string      | Bronze/Silver | Valor entregado como anticipo.                         | Control de anticipos.   |
| valor_amortizado         | string      | Bronze/Silver | Valor amortizado del anticipo.                         | Seguimiento financiero. |
| valor_pendiente_de       | string      | Bronze/Silver | Valor pendiente asociado a obligaciones contractuales. | Control financiero.     |
| saldo_vigencia           | string      | Bronze/Silver | Saldo presupuestal disponible en la vigencia.          | Gestión presupuestal.   |

# Acuerdo de Paz y Posconflicto

| Columna             | Tipo Origen | Nivel ETL          | Descripción                                                      | Uso                                |
| ------------------- | ----------- | ------------------ | ---------------------------------------------------------------- | ---------------------------------- |
| espostconflicto     | string      | Bronze/Silver/Gold | Indica si el contrato está asociado a programas de posconflicto. | Seguimiento de políticas públicas. |
| puntos_del_acuerdo  | string      | Bronze/Silver      | Punto del Acuerdo de Paz relacionado con el contrato.            | Evaluación de implementación.      |
| pilares_del_acuerdo | string      | Bronze/Silver      | Pilar estratégico del Acuerdo de Paz asociado.                   | Análisis de impacto.               |

# Representante Legal

| Columna                                    | Tipo Origen | Nivel ETL          | Descripción                                     | Uso                        |
| ------------------------------------------ | ----------- | ------------------ | ----------------------------------------------- | -------------------------- |
| nombre_representante_legal                 | string      | Bronze/Silver      | Nombre del representante legal del contratista. | Trazabilidad jurídica.     |
| nacionalidad_representante_legal           | string      | Bronze/Silver      | Nacionalidad del representante legal.           | Caracterización.           |
| domicilio_representante_legal              | string      | Bronze/Silver      | Domicilio registrado.                           | Validación administrativa. |
| tipo_de_identificaci_n_representante_legal | string      | Bronze/Silver      | Tipo de documento del representante legal.      | Identificación.            |
| g_nero_representante_legal                 | string      | Bronze/Silver/Gold | Género reportado del representante legal.       | Estudios de participación. |

# Información Bancaria

| Columna          | Tipo Origen | Nivel ETL     | Descripción                            | Uso                    |
| ---------------- | ----------- | ------------- | -------------------------------------- | ---------------------- |
| nombre_del_banco | string      | Bronze/Silver | Entidad bancaria utilizada para pagos. | Auditoría financiera.  |
| tipo_de_cuenta   | string      | Bronze/Silver | Tipo de cuenta bancaria registrada.    | Validación financiera. |

# Supervisión y Responsables

| Columna                               | Tipo Origen | Nivel ETL     | Descripción                                     | Uso                        |
| ------------------------------------- | ----------- | ------------- | ----------------------------------------------- | -------------------------- |
| nombre_ordenador_del_gasto            | string      | Bronze/Silver | Funcionario que autoriza el gasto.              | Auditoría administrativa.  |
| tipo_de_documento_ordenador_del_gasto | string      | Bronze/Silver | Tipo de documento del ordenador del gasto.      | Validación.                |
| nombre_supervisor                     | string      | Bronze/Silver | Supervisor designado del contrato.              | Seguimiento contractual.   |
| tipo_de_documento_supervisor          | string      | Bronze/Silver | Tipo de documento del supervisor.               | Identificación.            |
| nombre_ordenador_de_pago              | string      | Bronze/Silver | Responsable de ordenar los pagos.               | Auditoría financiera.      |
| tipo_de_documento_ordenador_de_pago   | string      | Bronze/Silver | Tipo documental del ordenador de pago.          | Validación administrativa. |
| n_mero_de_documento_ordenador_de_pago | string      | Bronze/Silver | Número de identificación del ordenador de pago. | Trazabilidad.              |

# Transparencia y Acceso Público

| Columna                     | Tipo Origen | Nivel ETL     | Descripción                                         | Uso                                |
| --------------------------- | ----------- | ------------- | --------------------------------------------------- | ---------------------------------- |
| urlproceso                  | object/url  | Bronze/Silver | Enlace directo al proceso en SECOP II.              | Navegación y verificación pública. |
| documentos_tipo             | string      | Bronze/Silver | Indica disponibilidad de documentos asociados.      | Control documental.                |
| descripcion_documentos_tipo | text        | Bronze/Silver | Descripción de los documentos asociados al proceso. | Auditoría documental.              |

---

# Transformaciones Planeadas

## Fechas

| Campo Origen                 | Campo Silver | Regla       |
| ---------------------------- | ------------ | ----------- |
| fecha_de_firma               | fecha_firma  | CAST a DATE |
| fecha_de_inicio_del_contrato | fecha_inicio | CAST a DATE |
| fecha_de_fin_del_contrato    | fecha_fin    | CAST a DATE |

## Valores

| Campo Origen       | Campo Silver    | Regla              |
| ------------------ | --------------- | ------------------ |
| valor_del_contrato | valor_contrato  | CAST DECIMAL(18,2) |
| valor_pagado       | valor_pagado    | CAST DECIMAL(18,2) |
| valor_facturado    | valor_facturado | CAST DECIMAL(18,2) |

---

# Datos Sensibles

Los siguientes campos no deberán exponerse directamente en APIs públicas o dashboards Gold.

| Campo                                   | Riesgo |
| --------------------------------------- | ------ |
| documento_proveedor                     | Medio  |
| identificaci_n_representante_legal      | Medio  |
| n_mero_de_documento_supervisor          | Medio  |
| n_mero_de_documento_ordenador_del_gasto | Medio  |
| n_mero_de_cuenta                        | Alto   |

---

# Reglas de Calidad

## nit_entidad

* Obligatorio
* No nulo

## id_contrato

* Obligatorio
* Único dentro del dataset

## valor_del_contrato

* Numérico
* Mayor o igual a cero

## fecha_de_firma

* Fecha válida

---

# Métricas Gold Planeadas

| Métrica                    | Fórmula                           |
| -------------------------- | --------------------------------- |
| total_contratado_entidad   | SUM(valor_del_contrato)           |
| total_contratado_proveedor | SUM(valor_del_contrato)           |
| cantidad_contratos         | COUNT(id_contrato)                |
| valor_promedio_contrato    | AVG(valor_del_contrato)           |
| porcentaje_ejecucion       | valor_pagado / valor_del_contrato |

---

# Linaje de Datos

| Campo Gold         | Origen             |
| ------------------ | ------------------ |
| total_contratado   | valor_del_contrato |
| cantidad_contratos | id_contrato        |
| valor_promedio     | valor_del_contrato |
| total_pagado       | valor_pagado       |
| total_facturado    | valor_facturado    |
|                    |                    |

# Campos Estratégicos para Contraduría

## Detección de concentración contractual

- nit_entidad
- proveedor_adjudicado
- documento_proveedor
- valor_del_contrato

## Seguimiento presupuestal

- valor_del_contrato
- valor_pagado
- valor_facturado
- saldo_cdp
- saldo_vigencia

## Análisis territorial

- departamento
- ciudad
- localizaci_n

## Análisis de modalidades de contratación

- modalidad_de_contratacion
- justificacion_modalidad_de
- tipo_de_contrato

## Seguimiento de ejecución

- estado_contrato
- fecha_de_inicio_del_contrato
- fecha_de_fin_del_contrato
- dias_adicionados

## Seguimiento del Acuerdo de Paz

- espostconflicto
- puntos_del_acuerdo
- pilares_del_acuerdo