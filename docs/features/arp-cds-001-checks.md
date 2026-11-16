# ARP-CDS-001 — Comprobaciones del primer borrador

**15-11-2026.** Estado: **solo borrador estructural / coherencia de fixtures**.

## Archivos nuevos

- `docs/decisions/ARP_reorientacion_arquitectura_funcional.md`: planteamiento general, sin cambios sustantivos; normalizados espacios finales.
- `docs/decisions/ARP_CDS_modelo_semantico_primera_integracion_Angular.md`: registro de D01–D11, sin cambios sustantivos; normalizados espacios finales.
- `docs/features/arp-cds-001.md`: candidata a especificación de físico, overlays y proyecciones.
- `schemas/cds/v1/*.schema.json`: tres esquemas JSON Schema, **candidatos no normativos**.
- `examples/demo/cds/*.yaml`: diccionario y overlays/proyecciones de la misma demo para tres runtimes.
- `examples/demo/sql/*.sql`: esquemas básicos por motor para entornos aislados.
- `fixtures/cds/v1/observations/*.yaml`: observaciones físicas simuladas para pruebas, **no fuente de verdad de una BD real**.
- `fixtures/cds/v1/manifest.json`: diez escenarios, positivos y negativos.
- `tools/check_cds_draft.py` y `tests/test_cds_draft.py`: comprobaciones de la estructura y un subconjunto de invariantes.

## Ejecución

Desde la raíz de `arp-contract`, con las dependencias ya declaradas en `tools/requirements.txt` (`jsonschema`, `PyYAML`):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_cds_draft.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

**Verificado en el paquete preparado:** 3 esquemas correctos, 2 observaciones físicas ilustrativas, 10 escenarios de fixture y 9 pruebas unitarias del nuevo borrador, todos correctos.

**Límites importantes:** este checker usa PyYAML únicamente para los archivos de ejemplo, **no** implementa el perfil de ingesta portable ni es un resolver ARP de producción. No conecta a una base de datos, no evalúa todos los posibles desacuerdos físicos, no hace CRUD, no mide concurrencia y no prueba los runtimes. Por tanto, NO hay ninguna conformidad Java/.NET/PHP ni una release nueva.

## Pasos siguientes

1. Revisar y aprobar (o corregir) la gramática y semánticas nuevas sin redefinir ARP-DICT-001.
2. Completar fixtures de resolución real, conflictos, autorización y ciclos de vida con resultados/errores exactos.
3. Ejecutar tests nativos contra esos fixtures en los tres repositorios, implementando sus puertos físicos propios.
4. Verificar los servicios, demos y el cliente Angular común; registrar evidencias exactas, sin publicar versiones parciales.

**Integración:** incorporar los archivos a una rama propia en `arp-contract`; no se han escrito en el repositorio GitHub por limitación de permisos del conector. No hacer merge antes de la revisión del contrato.

## Corrección de dos escenarios de revisión (PR #7)

- `derived-cannot-expand-fields` añade `internal_note` a la observación física
  simulada antes de intentar incluirlo en la proyección hija. El modelo lógico
  efectivo debe contenerlo y la proyección pública padre debe excluirlo; el
  rechazo prueba entonces **herencia restrictiva**, no inexistencia física.
- `unknown-physical-capacity` usa una observación **sintética de adaptador opaco**:
  `vendor_opaque_rating` no tiene `scalarType` ni límites numéricos verificados.
  El resultado de compatibilidad debe ser `not-verified`. Este nombre nativo
  **no se presenta como un tipo SQL válido de MariaDB**.
- Prueba de control complementaria: si un `INT8` verificado pierde solo su
  atributo redundante `maximum`, su rango sigue deduciéndose de `INT8` y debe
  seguir clasificándose como compatible con `0..10`. No confundir atributo
  ausente con capacidad desconocida.

Estas comprobaciones siguen siendo **estáticas y deliberadamente limitadas**;
la validación real de tipos nativos y de adaptadores no está implementada aquí.


## Ampliación: compatibilidad y actualización parcial de datos históricos

- `docs/features/arp-cds-001-compatibility-and-historical-data.md`: frontera
  de adaptadores físicos, representabilidad lógica, estado independiente de auditoría,
  PATCH de campos incluidos y controles de formulario ante datos históricos.
- `fixtures/cds/v1/compatibility.json`: vectores para rangos enteros exactos,
  tipos lógicos/físicos diferentes, restricciones intrínsecas/contextuales y
  capacidades no verificadas.
- `fixtures/cds/v1/historical-updates.json`: vectores de CREATE, UPDATE parcial,
  edición de cliente y auditorías sintéticas.
- `tools/check_cds_compatibility_draft.py` y
  `tests/test_cds_compatibility_draft.py`: oráculo **limitado a rangos enteros**
  e integridad de los casos compartidos; no runtime ni validación de BD real.

Ejecución adicional:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_cds_compatibility_draft.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Estos vectores propuestos no constituyen aún una adopción contractual por Java,
.NET o PHP; la formalización del protocolo de ejecución, restricciones no
enteras, concurrencia y metadatos de UI permanece pendiente.


## Integración del catálogo físico recuperado (ARP-CDS-PHY-001)

El único esquema físico candidato es `schemas/cds/v1/physical.schema.json`.
Los casos `fixtures/physical/v1` se validan contra ese mismo esquema; la
antigua variante de `schemas/physical/v1` deja de existir. El checker de
compatibilidad entera consume ahora `integerRange`, y la nulabilidad/longitud
no verificada continúa expresándose mediante omisión. Se mantienen pruebas
estáticas; no constituyen conformidad de los adaptadores reales.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_cds_draft.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_cds_compatibility_draft.py
```
