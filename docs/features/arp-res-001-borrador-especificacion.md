# ARP-RES-001 — Recursos lógicos declarativos y campos escalares

**Estado:** borrador técnico inicial para revisión en `arp-contract`; NO es un contrato aprobado ni publicado.
**Destino propuesto en el repositorio:** `docs/features/arp-res-001.md`.
**Dependencia indispensable:** catálogo de escalares de ARP-DICT-001 (`arp.dictionary/v1`).
**Alcance de esta fase:** contrato, esquema, fixtures y comprobaciones independientes; implementaciones PHP/Java/.NET después de aprobar la especificación.
**Política de publicación:** no crear etiquetas ni GitHub Releases hasta completar los módulos del MVP global de ARP.

## 1. Objetivo y frontera de responsabilidades

ARP permite que una aplicación o un módulo declare **recursos lógicos** y sus **usos de campos** mediante referencias a elementos de un diccionario ya resuelto. ARP reconoce identidad, estructura declarada, presencia, nulabilidad y validación escalar genérica. La aplicación conserva el significado empresarial, los datos, la identidad física de registros, la autorización, las operaciones, la concurrencia y la persistencia.

**El recurso no es una tabla ni implica CRUD.** Su identificador nombra una definición lógica; no es una clave primaria. Su descripción no crea rutas HTTP, entidades ORM, tablas, migraciones ni componentes UI.

### 1.1 Diseño objetivo (posterior, no perteneciente a este MVP)

- Campos que reutilizan estructuras compuestas de `ARP-DICT-002`, relaciones y referencias entre recursos, cuando se aprueben sus contratos.
- Reglas de composición de restricciones contextuales que estrechen las restricciones intrínsecas del diccionario, sin debilitarlas.
- Definición de vistas lógicas, metadatos de presentación (formularios, listas, literales, ayudas, navegación) y localización.
- Operaciones CRUD lógicas y puente a funciones de dominio registradas, con semántica explícita de autorización, contexto, concurrencia y persistencia en sus respectivos módulos.
- Adaptadores opcionales de HTTP, bases de datos, ORM, interfaces de usuario y verificaciones de almacenamiento.

### 1.2 MVP propuesto para `ARP-RES-001`

1. Registro explícito de fuentes JSON/YAML de recursos, sin convenciones de carpetas.
2. Definiciones con identificador cualificado de recurso y lista no vacía de campos escalares.
3. Cada campo referencia **un elemento ya presente** en un catálogo `ARP-DICT-001` recibido explícitamente.
4. Propiedades contextuales `required` y `nullable`, separadas entre sí; `label` y `description` opcionales sin efecto sobre la validación.
5. Construcción atómica, determinista e inmutable de un catálogo de recursos, rechazo de duplicados y referencias inexistentes.
6. Resolución de descriptores y validación de un mapa completo de entrada según las reglas de presencia, nulabilidad y validación/normalización delegada al diccionario.
7. Fixtures portables, resultados y errores reproducibles entre PHP 8.5+, Java 25 y .NET 10.

**No incluido en este MVP:** actualizaciones parciales/PATCH; defaults; `readOnly`/`immutable`; campos calculados; restricciones contextuales adicionales a presencia/nulabilidad; relaciones; herencia; estructuras compuestas; selección de columnas; acceso físico; transacciones; endpoints; consultas; autorización; handlers; reglas de negocio; vistas y presentación. Un campo válido no autoriza guardar nada.

## 2. Identidad, fuentes y catálogos

- El `resource.id` tiene la misma gramática cualificada, longitud máxima (128 ASCII) y sensibilidad a mayúsculas de los identificadores de `ARP-DICT-001`.
- Un campo `name` es un segmento simple ASCII `[A-Za-z][A-Za-z0-9_-]*`, máximo propuesto 64 caracteres. Es una identidad **local al recurso** y sensible a mayúsculas.
- Una referencia `elementId` usa la gramática cualificada de `ARP-DICT-001` y debe resolverse exactamente en el catálogo de diccionario seleccionado.
- Los proveedores entregan instantáneas inmutables y sus identificadores de procedencia (`providerId`/`sourceId`), sin introducir semántica de directorios, módulos, inquilinos o rutas.
- La aplicación selecciona explícitamente fuentes activas **y** el catálogo de diccionario correspondiente al mismo ámbito lógico. No hay catálogo global implícito ni mezcla de definiciones entre aplicaciones/tenants.
- Cualquier `resource.id` duplicado entre fuentes activas invalida la construcción, incluso si las definiciones coinciden. Los campos duplicados dentro de un recurso también son inválidos. No hay sustitución, herencia ni precedencias implícitas.
- Si falla el parseo, una referencia o una definición, **no se publica un catálogo parcial**. La aplicación puede conservar una generación previa válida, identificada como tal.
- El orden de entrada de fuentes y recursos no determina la semántica. Los descriptores se enumeran por ID de recurso ascendente; los campos por `name` ascendente en proyecciones y errores, salvo que un contrato posterior añada orden de presentación independiente.

## 3. Documento declarativo (formato PROPUESTO)

**Propuesta de formato:** `arp.resource/v1`. El identificador todavía **no está aprobado** ni es prueba de publicación. Se propone aprovechar el perfil de admisión JSON/YAML **portable** de `ARP-DICT-001` (rechazo de claves duplicadas, tipos implícitos propios de YAML, alias, tags y extensiones), con esquema cerrado y límites de seguridad que deberán consolidarse antes de implementar.

### 3.1 Ejemplo ilustrativo en JSON

```json
{
  "apiVersion": "arp.resource/v1",
  "resources": [
    {
      "id": "catalog.item",
      "label": "Item",
      "fields": [
        { "name": "code", "elementId": "catalog.productCode", "required": true, "nullable": false },
        { "name": "amount", "elementId": "finance.amount", "required": false, "nullable": true }
      ]
    }
  ]
}
```

`catalog.productCode` y `finance.amount` son referencias **de ejemplo** a elementos definidos por la aplicación en documentos separados de diccionario. No son vocabulario integrado en ARP; la fuente de recursos será inválida si esas referencias no existen en el catálogo elegido.

### 3.2 Forma cerrada propuesta

| Nivel | Propiedad | Tipo / significado |
| --- | --- | --- |
| Documento | `apiVersion` | Obligatorio; cadena `arp.resource/v1` |
| Documento | `resources` | Obligatorio; array no vacío de objetos |
| Recurso | `id` | Obligatorio; identificador cualificado |
| Recurso | `fields` | Obligatorio; array no vacío de campos |
| Recurso | `label`, `description` | Cadenas no vacías opcionales; texto sin semántica operativa |
| Campo | `name` | Obligatorio; identificador simple dentro del recurso |
| Campo | `elementId` | Obligatorio; referencia cualificada a escalar existente |
| Campo | `required` | Booleano opcional, **false** por defecto |
| Campo | `nullable` | Booleano opcional, **false** por defecto |
| Campo | `label`, `description` | Cadenas no vacías opcionales; contexto descriptivo del uso |

Se rechazan todas las propiedades desconocidas y todos los `null` donde no se hayan permitido explícitamente. No se aceptan redefiniciones de `type`, `constraints` ni `enumValues` dentro de un campo; la autoridad intrínseca permanece en el diccionario. La resolución genera un descriptor independiente de referencias o copias mutables del llamante.

## 4. Semántica de campos y de validación de entrada

- **Ausencia** y **`null`** no son equivalentes: `required` determina si debe existir la clave; `nullable` determina si se admite `null` cuando la clave está presente.
- Si el campo está presente con valor **no nulo**, se utiliza **exactamente** la validación portable de `ARP-DICT-001`. No se coercionan tipos, no se redondea, no se recortan cadenas y no se toleran restricciones intrínsecas más débiles.
- Una validación completa recibe un **objeto** cuyos nombres de propiedades son nombres de campo de la definición de recurso. No son automáticamente columnas, JSON público de una API ni parámetros de una operación de negocio.
- Las claves no declaradas se rechazan; un objeto vacío solo es válido si ningún campo es obligatorio. Las claves duplicadas del JSON de entrada se rechazan en la capa de admisión (no se permite sobrescribir silenciosamente una clave).
- En una validación satisfactoria, el resultado normalizado incluye **únicamente los campos presentes**. Los campos ausentes se mantienen ausentes y los valores `null` permitidos permanecen `null`; los demás valores usan la normalización del diccionario.
- Una validación fallida no entrega un mapa de valores normalizados parcial. Los problemas se reportan ordenados por nombre de campo; las infracciones intrínsecas de un campo respetan el orden de `ARP-DICT-001`.

### 4.1 Matriz mínima de presencia/nulabilidad

| `required` | `nullable` | Ausente | Presente con `null` | Presente con valor correcto |
| --- | --- | --- | --- | --- |
| false | false | Válido | Inválido | Válido |
| false | true | Válido | Válido | Válido |
| true | false | Inválido | Inválido | Válido |
| true | true | Inválido | Válido | Válido |

### 4.2 Proyección de resultado para pruebas (propuesta)

Éxito:

```json
{
  "valid": true,
  "normalizedValues": { "amount": "1.23", "code": "P001" },
  "issues": []
}
```

Fallo:

```json
{
  "valid": false,
  "issues": [
    { "code": "RESOURCE_REQUIRED_FIELD", "field": "code" }
  ]
}
```

La forma exacta de transmitir una infracción interna de `ARP-DICT-001` dentro de un error de recurso (código original, campo y causa estructurada) **queda por fijar en las fixtures**, antes de escribir los runtimes. Nunca se sustituye una infracción de tipo o de precisión por un error genérico que pierda su significado. Estos objetos son proyecciones neutrales para conformidad, no tipos de retorno impuestos a los tres lenguajes.

## 5. Operaciones conceptuales y errores (propuestas)

- `buildResourceCatalog(activeSources, dictionaryCatalog)` → catálogo inmutable o incidencias de definición; operación atómica.
- `resolveResource(resourceId)` → descriptor completo o incidencia de recurso inexistente.
- `validateResourceValues(resourceId, values)` → éxito con valores canónicos o incidencias; **no guarda datos**.

Familias de error por concretar en los casos de prueba:

| Código propuesto | Situación |
| --- | --- |
| `RESOURCE_DOCUMENT_INVALID` | JSON/YAML inválido, clave repetida, forma inesperada o sintaxis prohibida |
| `RESOURCE_FORMAT_UNSUPPORTED` | `apiVersion` desconocido o ausente en documento raíz válido |
| `RESOURCE_DEFINITION_INVALID` | ID, nombre, campo o propiedad mal declarados |
| `RESOURCE_DUPLICATE_RESOURCE` | Recurso repetido en fuentes activas |
| `RESOURCE_ELEMENT_NOT_FOUND` | `elementId` inexistente en el catálogo de diccionario entregado |
| `RESOURCE_NOT_FOUND` | Recurso inexistente al resolver/validar |
| `RESOURCE_REQUIRED_FIELD` | Falta un campo declarado como obligatorio |
| `RESOURCE_NULL_NOT_ALLOWED` | Se recibe `null` sin permiso contextual |
| `RESOURCE_UNKNOWN_FIELD` | El objeto contiene un campo no declarado |
| `RESOURCE_VALUE_INVALID` | El diccionario ha rechazado un valor escalar; conservar su código y detalles semánticos |
| `RESOURCE_LIMIT_EXCEEDED` | Límite de admisión o presupuesto de seguridad excedido |

La clasificación de errores de admisión, duplicados, límites y valores deberá ser **observable e idéntica** en los tres runtimes. Los detalles internos de parser, stack traces y mensajes localizados no forman parte de la proyección portable.

## 6. Reglas de seguridad e interoperabilidad

1. Perfil de JSON/YAML portable basado en `ARP-DICT-001`, con límites explícitos y documentados; no ejecutar tags, alias, expresiones, funciones ni constructores.
2. Las fuentes de recursos son datos declarativos no confiables. El proveedor solo transmite datos; su identidad de procedencia es suministrada por la aplicación, no por un campo falsificable del documento.
3. No aceptar datos desconocidos por accidente ni aplicar defaults que creen valores empresariales.
4. Referencias al diccionario resueltas contra **una instantánea completa y concreta**, sin buscar automáticamente en un catálogo global distinto.
5. La mutación de descriptores o resultados por el consumidor no altera el catálogo resuelto ni afecta a otros ámbitos.
6. Sin ejecución de negocio, autorización, persistencia ni efectos laterales en los métodos del MVP.
7. Las validaciones son deterministas e independientes del orden de fuentes, entorno local, zona horaria y proveedor de almacenamiento.

**Presupuestos iniciales por decidir expresamente antes de aprobar el contrato:** límites por fuente/recurso/campos y comportamiento de referencias que apunten a versiones distintas de catálogos del diccionario. No se inventan cifras ni reglas de migración basadas en la implementación de un solo lenguaje. El límite de bytes y la profundidad de `ARP-DICT-001` constituyen la referencia técnica de partida, pero no quedan automáticamente heredados sin aprobación.

## 7. Inventario mínimo de fixtures compartidas

Los casos deberán contener fuentes originales, catálogo previo de diccionario, operación, resultado semántico esperado y estado de ejecución. Como mínimo:

1. Construcción válida de recursos con varios campos y varias fuentes; resolución de descriptores completos, incluyendo campos opcionales y textos contextuales.
2. Reconocimiento de `arp.resource/v1` y rechazo de formatos, sintaxis, claves y propiedades desconocidas.
3. Validación de identidades; recursos duplicados entre fuentes; campos duplicados dentro de un recurso; referencias inexistentes.
4. Construcción atómica: un fallo impide publicar el conjunto; generación válida anterior no se altera ni se confunde con una fallida.
5. Los cuatro casos de la matriz de presencia/nulabilidad, incluidos valores no nulos válidos e inválidos.
6. Rechazo de claves desconocidas, raíz de valores no objeto, claves repetidas y tipos no permitidos.
7. Delegación real a los 17 tipos escalares ya existentes: tipo, restricciones exactas, fechas/horas, Unicode, Base64 y normalización; se reutiliza la autoridad del diccionario, **sin copiar sus expectativas**.
8. Determinismo ante reordenación de fuentes, recursos y campos; aislamiento de catálogos y defensa frente a mutaciones.
9. Límites de recursos y adversarios JSON/YAML, una vez aprobados los presupuestos concretos.
10. Dos ámbitos independientes con un mismo recurso ID, pero definiciones distintas; no debe haber contaminación entre contextos.

## 8. Criterios de aceptación y plan operativo

**Primero, cerrar el contrato** en `arp-contract`, mediante una PR normal (sin publicación):

- Revisar y fijar las decisiones explícitamente pendientes de este borrador.
- Aprobar un identificador de formato y un JSON Schema cerrado; adoptar de manera verificable el perfil YAML/JSON portable.
- Construir el manifiesto y las fixtures con salidas exactas para cada familia de fallo, además de las pruebas estructurales independientes.
- Verificar que la especificación, el esquema y las fixtures coinciden; documentar comandos y resultados, sin atribuir pruebas no realizadas.

**Segundo, implementar** por separado en `arp-php`, `arp-java` y `arp-dotnet`:

- Consumir el catálogo de diccionario existente; evitar duplicar validadores escalares.
- Registrar fuentes, construir y resolver catálogo de recursos, validar valores.
- Ejecutar todas las fixtures compartidas y pruebas propias de aislamiento, inmutabilidad y seguridad.
- Registrar solo incidencias reales y resultados observados; no introducir otra revisión/etiqueta por rutina.

**Tercero, una comprobación de integración** con un módulo de demostración de la aplicación consumidora que reutilice un elemento del diccionario en dos recursos o usos con distinto `required`/`nullable`, sin almacenamiento ni endpoints obligatorios.

## 9. Riesgos y decisiones de revisión

- **No confundir recurso con tabla/CRUD:** ninguna propiedad de recurso concede persistencia, autorización ni acciones.
- **No importar estructuras antes de `ARP-DICT-002`:** se prevén las referencias futuras, pero se implementan solo campos escalares.
- **No debilitar restricciones intrínsecas:** el único contexto del MVP es presencia y nulabilidad; estrechamiento adicional exigirá reglas formales.
- **No confundir versiones:** `arp.resource/v1` es una generación *propuesta de formato*, no una versión Git que deba publicarse ahora.
- **Necesita aprobación contractual:** nombres exactos de errores/proyecciones, presupuestos de admisión y relación futura entre recursos y estructuras. Son decisiones del contrato común, no de PHP/Java/.NET.

**Referencia principal:** `arp-contract/docs/architecture.md`, en particular §§4–9, y `docs/features/arp-dict-001.md`, en particular §§3, 4, 6 y 7, consultados en el commit `4c0f4bd0337c01c15a036910b6462e6f0e674927`.
