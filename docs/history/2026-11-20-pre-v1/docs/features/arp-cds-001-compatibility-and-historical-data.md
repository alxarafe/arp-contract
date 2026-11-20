# ARP-CDS-001 — Compatibilidad física, datos históricos y actualizaciones parciales

**Estado:** borrador de contrato y casos compartidos para revisión; sin formato ni runtime publicado.
**Fecha:** 2026-11-15. **Dependencia:** `ARP-DICT-001` y [`arp-cds-001.md`](arp-cds-001.md).
**Decisiones funcionales:** acordadas en conversación; las estructuras de fixture y las semánticas técnicas son propuestas verificables, todavía no normativas.

## 1. Identificación del motor y frontera de responsabilidades

- La aplicación registra un **proveedor de metadatos físicos** asociado a una conexión. El proveedor conoce el motor y su versión mediante información confiable de la conexión, contrastada con la configuración del anfitrión; no infiere el motor a partir de PHP, Java o .NET.
- Un mismo anfitrión puede registrar varios proveedores/conexiones. ARP no impone un motor único.
- El adaptador entrega hechos físicos normalizados **verificados**: tipo y límites representables, longitud en sus unidades reales, precisión/escala, nulabilidad, claves y otras capacidades comprobables. Debe conservar la procedencia física. Si no puede demostrar una propiedad, la declara desconocida; nunca inventa un rango.
- El núcleo semántico resuelve el diccionario, el overlay y las propiedades verificadas. Su lógica de compatibilidad no contiene nombres de dialectos SQL.
- Para una escritura gestionada, `not-verified` **no equivale** a capacidad de escritura segura. Una aplicación puede proporcionar un adaptador/handler delegado bajo su propia responsabilidad y validación.

## 2. Compatibilidad estructural: no exigir identidad de tipos

Para un campo, llamamos **D** al conjunto exacto de valores aceptados por el tipo lógico de `ARP-DICT-001`, sus restricciones intrínsecas y todas las restricciones contextuales aplicables; **P** es el conjunto de valores que el almacenamiento físico puede representar **sin pérdida semántica**, según evidencias verificadas del adaptador.

- `compatible`: se demuestra `D ⊆ P`, incluidas conversiones, precisión y demás dimensiones relevantes. **No exige** que el identificador de tipo lógico coincida con el físico.
- `incompatible`: se demuestra que algún valor permitido por D no puede almacenarse en P sin pérdida, o que existe una contradicción estructural demostrable. No basta con que D y P tengan algún solapamiento.
- `not-verified`: falta información para demostrar cualquiera de los anteriores. No se interpreta como `compatible`.
- Las declaraciones intrínsecas del diccionario no se modifican. Una especialización contextual debe restringir el conjunto permitido, nunca agrandarlo. Un conjunto D vacío o una contradicción interna es error de definición; no es una compatibilidad exitosa vacía.

**Ejemplo:** diccionario `INT16` con ámbito contextual `0–10` y columna verificada MariaDB `TINYINT SIGNED` (`INT8`) → `compatible`. El mismo `INT16` **sin** esa restricción → `incompatible` con la columna `INT8`. PostgreSQL `SMALLINT` (`INT16`) admite ambos. No usar redondeos, conversiones implícitas con pérdida, zonas horarias inferidas ni longitud en bytes como sustituto de caracteres.

Los fixtures incluidos ahora solo ejercitan **intervalos enteros exactos** y ausencia de evidencias. No pretenden demostrar compatibilidad completa de `DECIMAL`, `STRING`, Unicode, colaciones, `DATE`/`DATETIME`, `NULL` o claves; deben incorporarse antes de declarar el contrato general normativo.

## 3. Conformidad de los datos existentes: verificación independiente

Una estructura compatible **no demuestra** que los registros preexistentes cumplan D. El estado de auditoría de un conjunto de datos es independiente:

- `not-verified`: no se ha auditado íntegramente una instantánea de datos, o no existe evidencia vigente de esa auditoría.
- `nonconforming`: se ha constatado al menos un registro que incumple el modelo lógico actual. Una comprobación parcial basta para demostrar **existencia** de incumplimiento.
- `conformant`: una auditoría completa y vigente de la instantánea considerada no ha encontrado incumplimientos. Las modificaciones posteriores pueden invalidar esa evidencia.

La auditoría se ejecuta explícitamente (por ejemplo, al migrar o a petición del operador), no recorre toda la tabla en cada carga ni en cada petición. El informe debe permitir identificar los registros infractores y no incluir datos sensibles sin autorización. ARP **no corrige, borra ni transforma** datos históricos automáticamente por declarar nuevas restricciones.

## 4. Semántica de CREATE y UPDATE parcial

- **CREATE** aplica las restricciones vigentes a los campos nuevos, tras resolver reglas de presencia, nulabilidad y defaults que se definirán en un contrato específico. Nunca admite `rating=11` si el rango efectivo es `0–10`.
- **UPDATE parcial:** los campos **ausentes** no se reescriben ni se validan individualmente por mera lectura. Cada campo **incluido** en el PATCH es una solicitud explícita de escritura y debe superar sus restricciones vigentes, incluso si el valor enviado coincide con el dato persistido. La comparación client-side es solo una optimización; el servidor no confía en ella.
- Enviar `null` no equivale a omitir el campo: pide expresamente escribir nulo, sujeto a la nulabilidad permitida. En el ejemplo `rating` físico no admite `null`.
- Se evalúan además las reglas de negocio dependientes, permisos, invariantes, integridad relacional y requisitos de concurrencia aplicables. Esas reglas pueden rechazar toda la operación aunque los campos incluidos sean válidos. No se declara automáticamente válido el registro completo.
- El mecanismo de protección frente a actualizaciones concurrentes (versión/ETag u otro) se especificará al formalizar CRUD. Esta propuesta no autoriza sobrescrituras silenciosas ni actualizaciones ciegas.

Por ejemplo, con un registro histórico `{code: "A", rating: 11}` y restricción `rating` entre 0 y 10:

| Operación | Resultado de validación del rango |
| --- | --- |
| `PATCH {code: "B"}` | Admitido; `rating=11` permanece intacto, sujeto a reglas dependientes |
| `PATCH {rating: 8}` | Admitido |
| `PATCH {rating: 11}` | Rechazado por valor inválido, aun si coincide con el persistido |
| `PATCH {rating: 12}` | Rechazado |
| `PATCH {rating: null}` | Rechazado en esta columna no nula |
| `CREATE {code: "A", rating: 11}` | Rechazado |

## 5. Metadatos neutrales y comportamiento del formulario

El cliente recibe las restricciones **vigentes**, el registro original y, si puede demostrarse, una advertencia de incumplimiento histórico. La representación visual debe distinguir un **valor almacenado** de un **valor permitido para introducir cambios**:

1. En modo lectura o al abrir edición, se puede mostrar `rating=11` como **valor histórico**, sin añadir 11 al catálogo de opciones permitidas.
2. Si `rating` permanece sin modificar, su incumplimiento no bloquea por sí solo el envío de cambios válidos en `code` u otros campos.
3. Al modificar `rating`, el control solo acepta valores finales de `0–10`; para un entero discreto pequeño se puede usar una lista cerrada. El cliente previene la selección/introducción de `11` o `12`, no se limita a advertir al guardar.
4. Tras pasar de `11` a `8`, el campo ya no ofrece `11` para volver a seleccionarlo durante esa edición. **No** se restaura la opción histórica por ser el valor original.
5. Cancelar **toda** la edición sin guardar restaura la lectura del original, incluso su `11`; ello no escribe el dato. Un intento no aceptado por el control no constituye una modificación guardable.
6. El cliente envía únicamente los campos cuyo valor finalmente aceptado cambió; nunca envía de nuevo un `11` histórico como parte de un PATCH de otro campo.
7. La condición de poder guardar se calcula sobre los **cambios** y reglas dependientes, no directamente sobre el `form.valid` del registro completo. La semántica es neutral y debe poder implementarse en Angular u otro cliente.

**Límite de la garantía UI:** para controles con escritura libre, pueden existir estados transitorios mientras se teclea (vacío, decimal incompleto, composición). El control no aceptará ni enviará como valor final uno fuera del dominio. Esto no elimina la validación autoritativa del backend.

## 6. Fixtures e implementación posterior

Los vectores de [`fixtures/cds/v1/compatibility.json`](../../fixtures/cds/v1/compatibility.json) y [`fixtures/cds/v1/historical-updates.json`](../../fixtures/cds/v1/historical-updates.json) expresan ejemplos de interoperabilidad **pendientes de ejecución en cada runtime**. El checker Python es una herramienta de integridad de fixtures y un pequeño oráculo limitado a enteros, no es motor ARP de producción.

Pendiente antes de publicar contrato de comportamiento: esquema neutral de metadatos de formularios y diagnóstico histórico; tipo/longitud/precisión completos; temporalidad y Unicode; semántica definitiva de PATCH; concurrencia; reglas con dependencias, autorización y contratos de transporte. No se publicará versión ni se afirmará conformidad nativa con estos vectores por el mero hecho de introducirlos.
