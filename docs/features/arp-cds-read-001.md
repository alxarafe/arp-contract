# ARP-CDS-READ-001 — Cierre propuesto del núcleo CDS de lectura

**Estado:** candidato para aprobación por revisión; no aprobado automáticamente por este documento ni publicado.
**Base:** CDS-001, CDS-PHY-001, D01–D11 y la ampliación de compatibilidad/históricos. DICT-001 no cambia.
**Objetivo:** hacer implementable de forma equivalente el recorrido tabla plana → observación física verificada →
modelo lógico efectivo → proyección explícita. Esta tarea no modifica runtimes ni declara conformidad nativa.

## 1. Decisiones revisadas y alcance propuesto

Las tres gramáticas de autoría siguen siendo exclusivamente `arp.physical/v1`, `arp.logical/v1` y
`arp.projection/v1`, con sus esquemas existentes bajo `schemas/cds/v1/`. No aparece un formato de recurso/entidad
nuevo. `models` en los resultados es una vista derivada e inmutable del mismo modelo lógico, no otra autoría.
El esquema nuevo `read-result.schema.json` describe únicamente resultados candidatos para pruebas, no HTTP.

| Decisión antes pendiente | Cierre propuesto para este corte |
| --- | --- |
| Identidad y referencias | Instantánea suministrada explícitamente; espacios separados físico/lógico/proyección |
| Ingesta portable | Adopción explícita del perfil JSON/YAML DICT-001 y presupuestos adicionales de este corte |
| Especialización contextual | Solo intervalos enteros inclusivos, sin debilitamiento; resto fuera del perfil |
| Compatibilidad demostrable | Contención exacta entre intervalos enteros; otras combinaciones `not-verified` |
| Derivación | Resolución transitiva, ciclos rechazados, subconjuntos de campos/operaciones sin cambiar semántica |
| Resultado y errores | Proyección exacta, orden determinista, primer diagnóstico por fases y sin publicación parcial |
| Observación y generación | Proveedor del anfitrión; autoridad BD y pruebas reales separadas del resolver puro |

Este perfil resuelve descriptores y comprueba definiciones. **No consulta filas ni ejecuta LIST/GET**, ni implementa
CRUD, escrituras, DICT-002, RES-001, servicios, consultas, filtros, paginación o formularios. LIST/GET siguen siendo
las declaraciones ya existentes de una proyección, no permisos ni capacidades de ejecución adquiridas aquí.

## 2. Entradas y confianza

El resolver recibe un catálogo DICT-001 **ya validado** y una instantánea de observaciones físicas, overlays y
proyecciones registradas por el anfitrión. Cada documento posee un identificador estable de fuente/handle suministrado
por este. No hay descubrimiento global, búsqueda de archivos, resolución remota ni I/O en el resolver puro.
Los handles usados por los fixtures no añaden propiedades a la gramática de autoría ni fijan una API nativa.

Solo las fuentes activas proporcionadas participan. No se implementa un gestor de módulos; la aplicación decide
qué conjunto entregar. Una instantánea vacía es válida. Ninguna definición se expone como servicio por existir.
`source.provider`, dialecto, versión y hechos físicos proceden del proveedor confiable, nunca de una afirmación
arbitraria del cliente o del lenguaje del runtime. Las observaciones ilustrativas no prueban hechos de una BD.

### 2.1 Perfil de entrada y límites

Se adopta **expresamente para los documentos de este corte** el perfil JSON/YAML de DICT-001: UTF-8 válido, valores
Unicode escalares, claves de texto únicas, sin alias, anchors, tags, directivas ni múltiples documentos, y números
exactos. Se mantienen sus límites de 1 MiB por documento, profundidad de colecciones 128, token numérico 256,
exponente absoluto 128 y magnitud menor que 10^128. No usar un cargador YAML genérico como sustituto de ese perfil.
Los identificadores y demás formas se validan después con los tres esquemas existentes.

Límites adicionales propuestos: 256 documentos CDS activos en total, 2048 columnas por tabla y 64 proyecciones en
una cadena, contando raíz e hija. Los límites de presupuestos se comprueban antes de realizar trabajo no acotado.
Un límite excedido produce `CDS_READ_LIMIT`. Los límites enteros expresados como cadenas tienen máximo 4096
caracteres y gramática `-?(0|[1-9][0-9]*)`. No se convierte un valor exacto a float/double.
Los enteros JSON matemáticos, incluido `1.0` o `1e127`, conservan su valor exacto; no se limitan al entero de máquina.

## 3. Resolución e identidades

1. Validar todos los documentos contra su esquema. Se rechazan propiedades desconocidas y formatos incorrectos.
2. Construir índices independientes por tipo de documento. Un ID repetido dentro del mismo tipo se rechaza incluso
   con contenido igual; no hay precedencia ni sobreescritura. El mismo texto en tipos distintos no causa colisión.
3. `logical.physical` resuelve exactamente un ID físico de esa instantánea.
   **No exige `logical.id == physical.id`.**
4. Cada `fields.<nombre>` del overlay debe existir en la tabla observada. Su referencia `dictionary`, si existe,
   se resuelve en la instantánea de diccionario suministrada, sin otro catálogo global.
5. `source.entity` refiere al ID lógico; `source.projection`, al ID de otra proyección del conjunto suministrado.
   No se añaden referencias entre entidades ni se recorren claves externas para resolver recursos.

IDs, nombres y referencias son exactos y sensibles a mayúsculas; no se realiza case folding ni equivalencia Unicode
implícita. El adaptador verifica los nombres reales según su motor. Las comparaciones del núcleo no usan cultura.

### 3.1 Coherencia de la observación

El alcance es `kind: table`. Una vista válida para CDS más amplio está fuera de este corte, no es una tabla falsa.
Se rechazan nombres de columna repetidos, ordinales conocidos repetidos, intervalos invertidos o contradictorios
con un tipo entero verificado, geometría decimal con scale > precision, referencias locales inexistentes de PK,
índices o FK, nombres de índices/FK repetidos y aridad FK local/remota distinta. No se consulta la tabla referida
por una FK. Los ordinales omitidos no se inventan y no obligan a conocer los de las otras columnas.

Las listas de PK/índices/FK se conservan: ausencia significa desconocido y `[]`, ausencia observada. `nullable`,
`generated`, `identity` y cualquier otra propiedad opcional no reciben defaults. Un `null` no sustituye ausencia:
si el esquema no lo permite es inválido. Leer metadatos de una tabla no exige una PK; este corte no identifica filas.

## 4. Modelo lógico efectivo y restricciones

El modelo efectivo incluye **todas** las columnas físicas y solo añade las especializaciones del overlay. Los
campos se ordenan por puntos de código Unicode, equivalentemente por bytes UTF-8 válidos; no por UTF-16 ni locale.
La observación física conserva su orden y datos originales. Una columna no especializada no pierde su existencia.

Con referencia al diccionario, el tipo lógico y sus restricciones intrínsecas proceden del descriptor DICT-001;
el tipo físico no lo sustituye. Sin referencia se utiliza `scalarType` físico solo cuando está verificado. Si falta,
no se inventa STRING ni otro tipo: `type`, `constraints` e `intrinsicConstraints` se omiten y el campo es opaco.
Se conservan los 17 tipos del diccionario, incluyendo ENUM y sus literales. Los futuros controles de datos deberán
llamar a sus validadores existentes, no copiar regex, precisión, fechas, Unicode o Base64 al módulo CDS.

`intrinsicConstraints` conserva las restricciones del descriptor. Sin binding, el tipo/rango físico verificado
constituye la base lógica: se incorporan sus extremos enteros estrictamente más estrechos que el tipo; los extremos
redundantes se conservan en `physical`, sin duplicarlos en las restricciones derivadas. Para otros tipos físicos
conocidos la base exportada es `{}`, sin afirmar una compatibilidad que no se ha probado. Esto no recorta un dominio
lógico autorado: en ausencia de binding no existe otro dominio independiente que deba hacerse caber.
`contextualConstraints` aparece **solo si el overlay contiene `constraints`**, incluso cuando sea `{}`. `constraints`
es el conjunto efectivo cuando se conoce el tipo. `label`, `description`, `hint` se copian solo cuando el overlay los
declara; no se introduce una jerarquía nueva de defaults visuales o localización.

### 4.1 Especializaciones soportadas

Un contexto no vacío solo se admite para tipos enteros DICT-001, con `minimum` y/o `maximum` inclusivos enteros,
y cuando las restricciones intrínsecas describen un intervalo inclusivo entero o son un mapa vacío (`{}`). El intervalo
parte de
los límites intrínsecos del elemento o, sin binding, de la base física anterior. Los extremos omitidos se heredan.
El nuevo mínimo no puede ser menor que el intrínseco y el nuevo máximo no puede ser mayor. Una contradicción o dominio
vacío es error de definición.
Los extremos contextuales efectivos se exportan como cadenas enteras canónicas; `-0` se normaliza a `0`. El contexto
autorado original se conserva separado y nunca se reescribe. No se rellena un extremo omitido en el YAML del usuario.

Otras restricciones contextuales válidas en el esquema CDS amplio producen `CDS_READ_PROFILE_UNSUPPORTED`;
no se aceptan silenciosamente ni se califican de inválidas universalmente. Esto incluye intervalos fraccionarios,
exclusividad, multipleOf, límites de texto y composición con restricciones intrínsecas no intervalares.
Un elemento con esas restricciones intrínsecas sigue siendo admisible si no pide composición contextual: se
preserva íntegro y su compatibilidad queda `not-verified`. No se modifica ni debilita DICT-001.

### 4.2 Compatibilidad

Para intervalos enteros de este perfil se demuestra D ⊆ P usando aritmética exacta. P parte del tipo entero
físico verificado y de extremos observados, completos o parciales. Quitar un extremo redundante no elimina el
rango implícito de un INT8 verificado. Un nombre nativo que contenga «INT8» no verifica `scalarType`.

D que no cabe en P provoca `physical-incompatible`: **nunca se recorta D para fabricar compatibilidad**.
Si falta evidencia o el perfil no prueba todas las restricciones/dimensiones, se exporta `not-verified`, incluso
con nombres lógicos/físicos iguales. Igualdad de nombres no prueba longitudes, Unicode, precisión o semántica temporal.
Por eso un STRING en VARCHAR(12) no se anuncia compatible automáticamente. No se autoriza ninguna escritura.
La auditoría de valores históricos queda separada y no se ejecuta al resolver descriptores.

## 5. Proyecciones explícitas

Se respeta la gramática vigente: `fields` explícitos y `operations`. En este perfil solo se aceptan declaraciones
LIST y GET, incluido `operations: []`. CREATE/UPDATE/DELETE son válidas en el esquema CDS general pero están fuera
del perfil; producen `operation-not-allowed`. Una propiedad operations ausente sigue siendo un error de esquema.
No se cambia el significado ni el origen declarativo de CRUD ni se asignan automáticamente permisos.

La raíz selecciona exclusivamente nombres presentes en el lógico efectivo. Los nombres son literales; no hay
expansión de comodines ni recuperación por una ruta alternativa. La hija solo puede elegir campos y operaciones
de su origen inmediato; hereda transitivamente tipos, restricciones y metadatos y puede reordenar campos. No puede
recuperar una columna excluida aunque exista físicamente. Se detectan referencias cíclicas y se acota la profundidad.
No hay overrides de tipo, restricciones o presentación: la gramática actual no los ofrece en una proyección.

Una nueva columna física aparece en lógico efectivo tras regenerar, pero **ninguna proyección la incorpora** sin
modificar explícitamente su selección. Una referencia retirada produce error; no se elimina silenciosamente.
La compilación no publica un endpoint ni autoriza acceso a filas.

## 6. Resultados y diagnósticos candidatos

Éxito: `{valid:true, issues:[], models:[...], projections:[...]}`. Modelos y proyecciones se ordenan por ID con la
comparación Unicode indicada. `valid:true` significa que la resolución completa no encontró un error; puede
contener campos `not-verified` y no equivale a compatibilidad física global demostrada. Una incompatibilidad
comprobada produce el fallo íntegro de la instantánea, no un modelo parcial con `valid:true`.
Cada modelo contiene `id`, la observación `physical` completa y `fields` efectivos.
Cada proyección contiene `id`, `source` autorado, `entity` lógico resuelto, `fields` en el orden explícito y
`operations` en el orden declarado. No se añaden capacidades ejecutables.

Los campos lógicos contienen `name`, `physical`, `compatibility` y, cuando existen, `dictionary`, `type`,
`intrinsicConstraints`, `contextualConstraints`, `constraints`, `enumValues`, `label`, `description`, `hint`.
Los campos proyectados omiten `physical`, `intrinsicConstraints` y `contextualConstraints`; conservan el resto y
`nullable` solo si fue observado. No se filtran detalles de conexiones ni columnas excluidas a través de ese resultado.
Es una proyección derivada para conformidad, no un segundo modelo de entidades ni una especificación de HTTP.

Fallo: `{valid:false, issues:[{family,code,at}]}`. No incluye modelos/proyecciones parciales. `at` usa JSON Pointer
sobre el arnés: `/physical/<handle>`, `/logical/<handle>` o `/projections/<handle>`, con escapes `~0`/`~1`.
La fuente y su handle los registra el anfitrión; no son datos confiables aportados por el solicitante.

| Código candidato | Familia | Significado |
| --- | --- | --- |
| CDS_READ_SOURCE_INVALID | definition-invalid | Entrada no portable, sintaxis o Unicode inválidos |
| CDS_READ_LIMIT | definition-invalid | Presupuesto excedido |
| CDS_READ_SCHEMA_INVALID | definition-invalid | Documento fuera del esquema existente |
| CDS_READ_DUPLICATE_ID | definition-invalid | ID repetido en su espacio |
| CDS_READ_PHYSICAL_INVALID | definition-invalid | Observación internamente contradictoria |
| CDS_READ_REFERENCE_NOT_FOUND | definition-invalid | Referencia no resuelta en la instantánea |
| CDS_READ_UNKNOWN_FIELD | definition-invalid | Especialización de columna inexistente |
| CDS_READ_PROFILE_UNSUPPORTED | definition-invalid | Construcción válida más amplia no soportada por este corte |
| CDS_READ_CONSTRAINT_WEAKENING | definition-invalid | Contexto que relaja el dominio intrínseco |
| CDS_READ_CONSTRAINT_CONTRADICTION | definition-invalid | Dominio efectivo vacío |
| CDS_READ_REFERENCE_CYCLE | definition-invalid | Ciclo de proyecciones |
| CDS_READ_FIELD_NOT_EXPOSED | definition-invalid | Campo no disponible en el origen inmediato |
| CDS_READ_OPERATION_EXPANSION | definition-invalid | Hija amplía operaciones de su origen |
| CDS_READ_DOMAIN_NOT_REPRESENTABLE | physical-incompatible | D no está contenido en P verificado |
| CDS_READ_OPERATION_UNSUPPORTED | operation-not-allowed | Operación fuera del corte de lectura |
| CDS_READ_OBSERVATION_FAILED | execution-failure | El proveedor no pudo obtener la observación |
| CDS_READ_SNAPSHOT_CHANGED | execution-failure | La generación dejó de estar vigente antes de publicarse |

Se mantienen las cinco familias CDS. `invalid-data` no se emite aquí porque no se validan registros. Las incidencias
del proveedor son de ejecución, no errores de definición; nunca contienen SQL, credenciales o trazas. Los errores
internos del resolver no se ocultan como documentos inválidos. El oráculo puro no simula proveedores ni captura
fallos de programación como si fueran resultados correctos.

### 6.1 Orden observable

Se devuelve solo la primera incidencia. Para un conjunto ya decodificado: límite total; esquema e ID duplicado
por tipo físico/lógico/proyección y handle ordenado; coherencia física por handle; modelos por ID y campos por
nombre; proyecciones por ID y recorrido del origen antes de comprobar la hija. Dentro de cada columna física,
los extremos se examinan en orden `minimum`, `maximum`, independientemente del orden de propiedades JSON/YAML;
después se comprueban intervalo ordenado, límites del tipo y geometría decimal. Las columnas se recorren en orden
autorado, seguidas de PK, referencias de índices y FK, y unicidad de nombres de índices y de FK. Un error de esquema
se señala en el documento, sin depender del texto/orden de un validador JSON Schema de terceros.

La ingesta de un documento es una etapa independiente de la resolución. Si un anfitrión ofrece una entrada conjunta
de fuentes crudas, comprueba primero el límite total y después decodifica por tipo físico/lógico/proyección y handle
Unicode; solo tras completar esa etapa aplica las comprobaciones de resolución. En cada fuente se mantiene el
orden del perfil DICT-001: bytes, UTF-8, profundidad/tokens y sintaxis/Unicode. No se agrega una API de carga
obligatoria.

En campo: referencia; soporte contextual; mínimo, máximo, dominio no vacío; contención física. En proyección:
ciclo; límite; operaciones soportadas; referencia y resolución del origen; operaciones heredadas; selección de campos.
La primera fuente de un ID duplicado no gana: falla todo el conjunto. Reordenar registros de fuentes no cambia
el resultado cuando sus handles son los mismos. No se acumulan errores cuya precedencia dependa del lenguaje.

## 7. Proveedores, invalidación y pruebas de BD

La resolución pura parte de una observación suministrada y no demuestra su veracidad. Las demos posteriores usan
PostgreSQL para Java/.NET y MariaDB para PHP, conforme a D10; el núcleo no contiene SQL por dialecto.

El adaptador observa la tabla registrada bajo demanda, verifica motor/versión y conserva los datos del proveedor.
La invalidación explícita descarta la vigencia del físico y sus derivados. No se borra ni reescribe el overlay.
Tras invalidar, no se publica una nueva resolución basada en el físico antiguo; el siguiente uso regenera. Un fallo
no publica un conjunto parcial ni presenta una generación anterior como actual. Si se invalida durante la generación,
no se publica ese resultado y se informa `CDS_READ_SNAPSHOT_CHANGED` en `/snapshot`.

La implementación puede usar una generación local o un bloqueo, sin imponer formato de token ni API de caché.
Los lectores de una instantánea pura inmutable conservan su objeto; eso no acredita que siga siendo el esquema
actual para una consulta SQL. La coherencia distribuida/entre tenants queda fuera; no se promete detección de DDL
externo sin invalidación explícita. Aislamiento entre catálogos del anfitrión sigue siendo obligatorio.

`database-cases.json` separa pruebas que necesitan BD real: creación en un ámbito desechable propio, observación,
columna añadida tras invalidación, columna especializada retirada, fallo de conexión y generación invalidada.
El contador de observaciones cuenta invocaciones del proveedor de tabla, no sentencias SQL.
Los hechos portables esperados son exactos; nombre del ámbito y engineVersion se contrastan con configuración y
consulta independiente, no con constantes inventadas. `nativeType` se conserva tal como se observó; no se impone
su ortografía entre drivers. No se sustituyen las observaciones reales por las ilustrativas del repositorio.
**No se han ejecutado esas pruebas en esta tarea.** No hay nuevos endpoints, servicios ni operaciones de datos.

## 8. Esquemas, fixtures y aceptación

- Entrada: los tres esquemas CDS existentes, sin otra gramática física o de entidad.
- Salida candidata: `schemas/cds/v1/read-result.schema.json`.
- `fixtures/cds/read/v1/cases.json`: resultados completos de resolución pura, positivos y negativos.
- `source-cases.json`: ingesta JSON/YAML equivalente y adversaria, separada de resolución y BD.
- `dictionary.json`: dos elementos escalares de prueba que reutilizan exclusivamente DICT-001.
- `database-cases.json`: obligaciones de integración real, **no ejecutadas por el oráculo**.
- `tools/check_cds_read_draft.py` y `tests/test_cds_read_draft.py`: oráculo acotado y regresiones semánticas.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_cds_read_draft.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
```

La aceptación nativa exige los mismos resultados exactos de los fixtures, las mismas reglas de presencia, orden,
referencias y rechazo, más límites/aislamiento/inmutabilidad y las 327 aserciones escalares previas. Deben mantenerse
BigInteger/Decimal o representaciones exactas equivalentes; las clases y nombres de APIs nativas pueden diferir.
La etapa pura puede cerrarse sin BD. La etapa proveedor solo se acredita después de ejecutar sus pruebas reales;
ninguna de las dos acredita LIST/GET de filas, CRUD, autorización de un servicio o conformidad general del runtime.

## 9. Descartado, aplazado y primera implementación

Descartado en este corte: igualar IDs físicos/lógicos; segundo formato de entidad; otra gramática física;
recortar dominios para hacerlos caber; traducir observaciones SQL desde el nombre del lenguaje; copiar validadores;
exponer automáticamente columnas; tratar metadatos como autorización.

Aplazado explícitamente: contextos no enteros/no intervalares, solver general de compatibilidad, required/null/defaults
lógicos, DICT-002, RES-001, relaciones y joins, vistas, consultas y lecturas de filas, filtros/paginación, formularios,
CRUD y su origen declarativo, servicios/transporte, migraciones, concurrencia distribuida e invalidación automática.
Esto no cambia las decisiones funcionales D01–D11; delimita una primera implementación comprobable.

**Primera tarea tras aprobar este candidato:** implementar el resolver puro en los tres runtimes, sobre sus
catálogos DICT-001 existentes, sin HTTP ni SQL obligatorio. Registrar las mismas entradas/salidas, ejecutar los
fixtures y las pruebas propias de aislamiento/precisión; conservar los contratos y comportamiento escalares.
Después implementar los proveedores reales del manifiesto separado y su ciclo de vida local. No anunciar ejecución
de proyecciones o nuevas capacidades Angular hasta que existan servicios de demo y pruebas reales para ello.

## 10. Validación de esta propuesta

En la rama `feature/arp-cds-read-001`:

- **80 escenarios de resolución y 11 de ingesta**, con expectativas independientes del resultado del oráculo.
- **106 pruebas Python correctas**: las 82 previas y 24 nuevas. Incluyen contención, inmutabilidad, ausencia/null,
  orden Unicode, límites, aislamiento, no exposición automática y rechazo de resultados parciales o familias erróneas.
- Los cinco verificadores anteriores y el verificador nuevo pasan. La comparación distingue booleanos/números y
  conserva enteros JSON matemáticos exactos; no utiliza float para los fixtures.
- Se elimina del antiguo oráculo la igualdad de IDs lógico/físico, manteniendo la comprobación de referencia y una
  regresión. No es un cambio de gramática. El perfil de ingesta compartido permite omitir solo su contador específico
  de elementos DICT al procesar CDS; el comportamiento por defecto DICT-001 permanece protegido por regresión.
- Los esquemas de autoría, contratos escalares, D01–D11 y runtimes permanecen intactos.
  Solo se enlaza este cierre desde CDS.
- El manifiesto de BD contiene cinco escenarios por motor (diez ejecuciones exigidas), **sin ejecutar** PostgreSQL,
  MariaDB, proveedores ni las bibliotecas nativas. No se declara conformidad nativa o física a partir de estos checks.

La revisión de cierre fija el orden de extremos físicos para que el primer error no dependa del orden de miembros.
Se han repetido las expectativas de los 80 casos invirtiendo recursivamente los objetos JSON y preservando arrays;
los resultados semánticos coinciden. Se conservan los 80 escenarios originales y los 11 casos de ingesta.

El cierre se prepara mediante commit y PR para revisión. La aprobación del alcance y sus límites/resultados
candidatos sigue correspondiendo a esa revisión; no se publica una versión ni se declara conformidad nativa.