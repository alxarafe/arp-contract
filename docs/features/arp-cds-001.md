# ARP-CDS-001 — Catálogo físico, modelo lógico y proyecciones públicas

**Estado:** borrador contractual para revisión, no publicado ni aprobado como sintaxis normativa.
**Fecha:** 2026-11-15. **Ámbito:** primer recorrido vertical conforme a D01–D11.
**Dependencia:** ARP-DICT-001. No modifica el contrato de los 17 tipos escalares.
**Marco:** `docs/architecture.md` y [`docs/decisions/ARP_CDS_modelo_semantico_primera_integracion_Angular.md`](../decisions/ARP_CDS_modelo_semantico_primera_integracion_Angular.md).

El subconjunto mínimo de lectura y sus cierres propuestos se especifican en
[ARP-CDS-READ-001](arp-cds-read-001.md). Reutiliza los tres esquemas de autoría existentes;
no los sustituye ni aprueba automáticamente los puntos más amplios de este documento.

## 1. Fronteras y finalidad

ARP aporta contratos neutrales y mecanismos reutilizables. Las aplicaciones aportan los modelos propios, el registro de fuentes y módulos, los validadores y operaciones de dominio, las autorizaciones y la persistencia. **ARP no es un ERP.** El diccionario debe poder usarse sin SQL ni Angular; ningún módulo implica necesariamente CRUD.

Recorrido acordado: **esquema físico real → descripción física generada bajo demanda → overlay lógico persistente → modelo lógico efectivo → proyección pública explícita → servicio validado/autorizado → cliente Angular genérico**.

Los formatos `arp.physical/v1`, `arp.logical/v1` y `arp.projection/v1` y los JSON Schemas adjuntos son **candidatos de diseño**. Su incorporación a este borrador no significa que sean formatos publicados o compatibles con los runtimes.

## 2. Descripción física generada (D01, D04)

El adaptador de almacenamiento observa una tabla o vista **real** y genera, si se necesita y no está disponible, su descripción física. La descripción es un artefacto regenerable y **no editable por el usuario**; la base de datos sigue siendo autoridad. No se inspecciona todo el esquema al arrancar ni se exige sondeo periódico.

La propuesta `arp.physical/v1` identifica un objeto físico y su fuente registrada (`provider`, `dialect`, `schema`, `name`) y describe columnas comprobadas. `nativeType` conserva la información propia del motor; `scalarType`, `integerRange`, `characterLength`, `nullable` y `primaryKey` solo se declaran cuando el adaptador **pueda verificarlos**. Omitir una propiedad significa **no verificado**, nunca compatible por defecto. No debe inferirse negocio del nombre de una columna.

La invalidación explícita tras DDL controlado invalida tanto la descripción generada como los catálogos lógicos efectivos y las proyecciones compiladas dependientes. El siguiente acceso regenera y verifica. Cambios SQL externos requieren invalidación explícita/manual. La regeneración fallida no publica un resultado parcial. Los detalles de atomicidad, concurrencia, caché multinstancia y alcance por tenant están pendientes.

La aplicación decide a qué módulo pertenece el recurso. Desactivar un módulo no borra tablas ni YAML del usuario; oculta los servicios activos. Reactivarlo exige resolver y validar de nuevo.

La ampliación física de `ARP-CDS-PHY-001` ya se expresa en un **único esquema**
`schemas/cds/v1/physical.schema.json`: incorpora `integerRange`, `characterLength`
con unidad, geometría decimal, ordinal, claves primarias compuestas, índices,
claves externas y columnas generadas, manteniendo `id`, `kind`, `source` y
`scalarType`. `primaryKey` se declara a nivel de objeto; desaparece el booleano
por columna. La fuente de verdad sigue siendo la BD real, no el fixture.
Véase [`arp-cds-phy-001-borrador.md`](arp-cds-phy-001-borrador.md).

## 3. Overlay lógico y compatibilidad (D01, D07)

El overlay persistente `arp.logical/v1` referencia un objeto físico e indica **solo las especializaciones del desarrollador**. El modelo lógico efectivo incorpora también **todas** las columnas físicas restantes, incluidas las nuevas tras regenerar; el overlay no se reescribe ni se pierde.

Un campo puede referir a un elemento de `ARP-DICT-001`, con sus restricciones intrínsecas, y añadir restricciones contextuales **más estrictas** y metadatos de presentación. Las restricciones intrínsecas, contextuales y capacidades físicas comprobadas se intersectan. Una incompatibilidad comprobada impide validar la definición afectada; una capacidad no verificada no se interpreta como compatibilidad demostrada. La semántica futura de presencia, `required`, `nullable` contextual y `default` requiere un contrato propio, no debe añadirse implícitamente al diccionario.

En la demo, `rating` admite **0–10** aunque MariaDB lo almacene en `TINYINT SIGNED` (-128 a 127) y PostgreSQL en `SMALLINT` (-32768 a 32767). La restricción de negocio pertenece al overlay, no a la descripción física.

## 4. Proyecciones públicas (D01–D03)

El modelo lógico es la base: no se impone una proyección principal artificial. `arp.projection/v1` propone `source.entity` o `source.projection`, `fields` **enumerados sin comodines** y `operations` explícitas de entre LIST, GET, CREATE, UPDATE, DELETE.

La proyección nunca se publica por mera existencia: la fuente/módulo han de estar activos y la aplicación debe habilitar su exposición. Los campos nuevos que aparezcan físicamente **no entran automáticamente en ninguna proyección pública**. Una derivada no puede recuperar campos excluidos, ampliar operaciones o permisos, alterar tipos ni relajar restricciones; sí podrá ajustar metadatos meramente visuales en una especificación posterior.

El servidor debe cerrar las rutas alternativas de divulgación (consultas, filtros, ordenaciones, navegación y serialización): no basta con ocultar una columna en Angular.

## 5. CRUD, validadores y seguridad (D02, D03, D06, D07)

Cada proyección puede declarar operaciones; declararlas **no concede permisos** ni garantiza que puedan gestionarse automáticamente. El primer CRUD gestionado se limita a una **tabla persistente con identificador inequívoco**, operación expresamente habilitada, restricciones verificadas y comprobación del servidor. Una escritura con reglas propias o entre varias tablas usa un manejador delegado registrado por la aplicación. Las vistas SQL no son automáticamente escribibles.

ARP no impone autenticación ni roles. Un consumidor verdaderamente público puede no tenerlos; si existen, la decisión confiable procede de la aplicación anfitriona. La validación de backend sigue siendo obligatoria y los validadores específicos se conectan mediante extensión registrada. El cliente Angular compartido consume metadatos neutrales, listados, formularios y acciones; jamás sustituye controles del servidor.

## 6. Diagnósticos (D08)

Las cinco familias acordadas son: **definición inválida**, **incompatibilidad física**, **dato inválido**, **operación no permitida** y **fallo de ejecución**. Los códigos, precedencia y transportes concretos requieren una especificación aparte y fixtures negativos. Ninguna excepción interna debe exponerse como traza por defecto. Las evidencias de compatibilidad son tres estados diferentes: compatible / incompatible / no verificado.

## 7. Ejemplos y pruebas compartidas (D09, D10)

Las definiciones comunes de `examples/demo/cds` se reutilizan en `arp-java/demo` (PostgreSQL), `arp-dotnet/demo` (PostgreSQL) y `arp-php/demo` (MariaDB). **No duplicar manualmente esos YAML en tres repositorios.** Las observaciones físicas de `fixtures/cds/v1/observations` solo son **vectores ilustrativos**: cada demo real debe regenerarlas desde su base de datos; nunca se toman como verdad sobre ella.

El mismo cliente Angular demostrará listados/formularios/acciones contra los tres backends. Los tests del checker incluidos aquí validan esquemas y coherencia interna de la propuesta, **no** un runtime, conexión SQL o conformidad de Java/.NET/PHP.

Casos contractuales necesarios para la siguiente fase:

1. Generación física perezosa desde motor real y regeneración posterior a invalidación.
2. Overlay con referencia válida al diccionario, restricción contextual y campos físicos no especializados conservados.
3. Nueva columna física visible en lógico efectivo e invisible en proyecciones públicas hasta selección explícita.
4. Derivación sin ampliación de campos ni operaciones; rechazos por campos retirados y referencias cíclicas.
5. Incompatibilidad física con conservación de YAML del usuario; distinguir propiedades no verificadas.
6. Módulo inactivo: no expone servicios, no borra definiciones; reactivación vuelve a comprobar.
7. Operaciones gestionadas sobre una tabla y delegadas para dominio; validar autorización y datos en backend.
8. Cinco familias de error y respuesta uniforme, con pruebas positivas y negativas por stack.
9. Una interfaz Angular consumiendo los tres servicios sin conocimiento de SQL ni lenguaje.

## 8. Pendientes de especificación — sin reabrir D01–D11

- Identidades, referencias, registro de proveedores y precedencia de fuentes.
- Perfil YAML seguro/portable; equivalencia estricta de YAML con JSON.
- Mapeo de tipos físicos y verificación de longitud/codificación/precisión/collation, PK, nulabilidad.
- Contradicciones de restricciones, presencia/null, defaults, errores y orden de resolución.
- Relaciones/consultas CDS, autorización de campos/filtros, paginación y derivación.
- Contrato de transporte de servicios y metadatos; ejecución y transacciones de CRUD gestionado.
- Invalidación atómica entre procesos y tenants, ciclo de vida de módulos.

**Orden cerrado (D11):** contrato y fixtures primero; implementaciones independientes después; demos por stack y finalmente Angular. **No publicar versión 0.1 ni tags parciales.** El objetivo global incluye también comportamientos, reglas, servicios y extensibilidad; este recorrido es solo el primer tramo.


## 9. Compatibilidad físico-lógica y valores históricos (ampliación propuesta)

La propuesta y sus vectores compartidos se documentan en
[`arp-cds-001-compatibility-and-historical-data.md`](arp-cds-001-compatibility-and-historical-data.md).
La compatibilidad exige **representabilidad completa del dominio lógico efectivo**
por el tipo físico verificado, no igualdad nominal de tipos. La conformidad de
los datos preexistentes se verifica por separado y no exige un escaneo al inicio.

En las actualizaciones parciales se validan los **campos incluidos**; los ausentes
no se reescriben ni se invalidan por datos históricos. El cliente conserva la
visualización de un valor histórico fuera de rango, pero, una vez que se edita
ese campo, solo admite valores nuevos válidos y no permite volver a elegir el
valor histórico inválido. Alta, cambios y backend conservan las restricciones.
Esta ampliación también sigue siendo **borrador no normativo**, sin evidencia de
conformidad de runtimes ni autorización para publicar una versión.