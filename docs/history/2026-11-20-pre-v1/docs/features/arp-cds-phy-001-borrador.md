# ARP-CDS-PHY-001 — Integración del modelo físico en ARP-CDS-001

**Estado:** borrador contractual unificado; no publicado, sin soporte de runtime demostrado.

**Decisiones funcionales:** D01, D04, D11 y ampliación de compatibilidad/datos históricos de ARP-CDS-001.

## Único contrato físico propuesto

El documento físico `arp.physical/v1` se define exclusivamente en
[`schemas/cds/v1/physical.schema.json`](../../../../../schemas/cds/v1/physical.schema.json).
El antiguo esquema alternativo `schemas/physical/v1/physical.schema.json` se elimina;
no deben coexistir dos gramáticas diferentes con el mismo `apiVersion`.

Se mantiene la estructura del primer borrador CDS: `id`, `kind` (`table` o `view`),
`source` (`provider`, `dialect`, `name` y `schema`/`catalog` opcionales) y `columns`.
`source.provider` identifica la conexión registrada por la aplicación;
`source.dialect` y `source.engineVersion`, cuando se declaran, provienen del adaptador
verificado, **nunca** se deducen del lenguaje de programación. `scalarType` es la
normalización escalar verificada, no una etiqueta de negocio. La identidad física
se obtiene de la fuente registrada y de la identidad completa del objeto.

Capacidades que se incorporan del borrador recuperado:

- `ordinal` opcional, cuando se verifica la posición de la columna.
- `integerRange` con límites decimales exactos, completos o parciales;
  se omite cualquier extremo desconocido, sin inventarlo. Un `scalarType`
  entero verificado conserva sus límites intrínsecos.
- `characterLength: {value, unit}`; `unit` distingue `CHARACTERS` y `BYTES`.
- `decimalGeometry: {precision, scale}` con `0 ≤ scale ≤ precision`.
- `nullable`, `identity`, `generated` como capacidades opcionales verificadas.
- `primaryKey` como **lista de columnas**, que permite claves compuestas; `[]`
  significa ausencia comprobada de clave y propiedad omitida significa no verificado.
- `indexes` y `foreignKeys` opcionales cuando su observación es completa y fiable.
  Una lista vacía significa ausencia observada, no dato desconocido.

Se eliminan del formato los atributos antiguos por columna `primaryKey: true`,
`minimum`/`maximum` y `maximumLength`, para evitar dos representaciones
contradictorias. Los ejemplos, pruebas y escenarios se han adaptado al formato único.

## Semántica y alcance

La BD real es la autoridad. El adaptador genera la descripción **bajo demanda**
y únicamente informa hechos comprobables; el YAML físico es regenerable,
no editable. La invalidación tras DDL controlado afecta a los derivados
lógicos y proyecciones compiladas. El DDL externo exige invalidación explícita;
no se promete detección autónoma ni introspección global al inicio.

El modelo lógico incorpora columnas físicas nuevas automáticamente; las
proyecciones públicas siguen requiriendo selección explícita. Las
especializaciones de usuario no se borran al cambiar el esquema o desactivar
un módulo. Los datos históricos inválidos se mantienen y se auditan por separado,
sin rebajar la validación de escrituras nuevas.

Los tipos SQL concretos, unidades de longitud, precisión, claves e índices
requieren proveedores por motor. Las reglas semánticas verificables incluyen
unicidad de nombres/ordinales según el proveedor, referencias locales existentes,
correspondencia de columnas de claves externas, intervalos ordenados y geometrías
decimales coherentes. El nombre original de SQL no se normaliza con un *case folding*
universal.

## Referencias y pruebas

- `fixtures/physical/v1/cases.json`: escenarios positivos y negativos adaptados.
- `fixtures/physical/v1/example.mariadb.yaml`: ejemplo del único esquema.
- `tests/test_physical_candidate.py`: estructura y coherencia local.
- `fixtures/cds/v1/observations/`: observaciones ilustrativas PostgreSQL/MariaDB.
- `tools/check_cds_draft.py` y `tools/check_cds_compatibility_draft.py`:
  pequeños oráculos estáticos de CDS y representabilidad entera.

**No demuestra** introspección de BD real, invalidación distribuida, CRUD,
resolución completa de Unicode/decimales/tiempos ni conformidad de Java/.NET/PHP.
La sintaxis continúa siendo candidata; no publicar versiones ni etiquetas.