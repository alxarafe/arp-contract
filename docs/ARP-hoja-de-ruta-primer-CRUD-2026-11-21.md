# ARP — Hoja de ruta para el primer CRUD completo

**Fecha de revisión:** 21 de noviembre de 2026
**Estado:** propuesta de planificación para revisión; no es un contrato aprobado ni una instrucción de cambiar código.
**Objetivo:** primer CRUD funcional, construido y revisado **primero en PHP/MariaDB** y, después, contrastado en
Java/PostgreSQL y .NET/PostgreSQL, demostrable mediante un único cliente Angular. **No** implica publicar una versión,
un tag ni un release de ARP.

## 1. Premisas que deben preservarse

1. ARP es un conjunto de capacidades **optativas**. No exige una estructura de directorios, framework, ORM, sistema de
   roles, formato de pantalla ni traslado del código empresarial a ARP.
2. La aplicación es propietaria de las entidades empresariales, decisiones de autorización, reglas de negocio, políticas
   transaccionales y consecuencias de las operaciones. ARP aporta contratos y mecanismos genéricos.
3. Se utilizan los nombres completos **Data Dictionary**, **Physical Definition**, **Logical Definition**,
   **Projection**, **Service Definition** y **Business Rule Definition**. No introducir nuevas abreviaturas hasta
   acordarlas. Los identificadores y archivos históricos existentes se conservan para no romper compatibilidad por un
   mero cambio terminológico.
4. Primer CRUD gestionado: **una tabla física existente con clave primaria demostrada**, proyección explícita,
   operaciones habilitadas, controles de servidor y soporte real de la capacidad de escritura por parte del adaptador.
   Operaciones con varias tablas, lógica particular, auditoría obligatoria o garantías no demostradas: **ejecución
   delegada**.
5. Las reglas implementadas por código pertenecen a la aplicación, idealmente aisladas de transporte y persistencia. ARP
   puede localizar, invocar y verificar el contrato de una regla **sin imponer su organización física**.
6. Definiciones y fixtures comunes primero en `arp-contract`; **PHP/MariaDB como primera implementación**, por la mayor
   experiencia del responsable del proyecto y la facilidad de revisión; Java y .NET después, con implementaciones
   independientes; demos por stack; finalmente **un único** cliente Angular. No duplicar definiciones comunes en los
   runtimes.
7. **La elección PHP/MariaDB como primer runtime ya estaba acordada; no es una decisión pendiente ni una recomendación
   nueva.** No abrir un ciclo de releases/tags parciales. «Publicar el primer CRUD» significa aquí disponer de un
   incremento integrado, revisado y demostrable en los repositorios de desarrollo, **no** distribuir una versión pública
   del producto.

## 2. Evidencia revisada en GitHub

Se ha examinado código y documentación de la rama `main` (no se han ejecutado tests en esta revisión):

| Repositorio | Commit de `main` examinado |
|---|---|
| `alxarafe/arp-contract` | `eb38cb96e6ccd218734df2a181908de46067e0c7` |
| `alxarafe/arp-java` | `91b5212aba176f97c37366166cb90fc7ae786bfb` |
| `alxarafe/arp-dotnet` | `2e6aa2ca2ba17b148b1f0873c58fcd2b38ddd6df` |
| `alxarafe/arp-php` | `ba69e467f55c6a8658361e32c3b350ce2d45a9aa` |

### 2.1. Existe ya

- Data Dictionary: parsers, descriptores, validadores escalares y fixtures en Java, .NET y PHP.
- Physical Definition: lectura/observación de metadatos de bases reales, almacenamiento del catálogo físico e
  invalidación, con distintos límites por motor.
- Logical Definition y Projection: esquemas candidatos, resolución y compatibilidad; proyecciones explícitas con
  operaciones listadas.
- LIST/GET: `ListGetHost` y lectores SQL reales en los tres runtimes; proveedores para PostgreSQL, MySQL/MariaDB y SQL
  Server, con cobertura y limitaciones específicas. Las pruebas documentadas son históricas, no reejecutadas en esta
  revisión.
- Contratos candidatos de operaciones/servicios: semántica de UPDATE parcial, conflictos por campo, invocación y
  resultados, con fixtures y verificadores estáticos.
- Demo Angular común: navegación y exploración de diccionario contra tres backends; **no** una demostración de CRUD
  activo.

### 2.2. Aún no queda acreditado como funcionamiento completo

- CREATE, UPDATE y DELETE gestionados que escriban realmente en una base de datos a través del contrato común.
- Un mecanismo neutral de escritura y su límite transaccional demostrado por los adaptadores.
- La decisión cerrada del origen declarativo/registro del CRUD ejecutable y la semántica completa de CREATE y DELETE.
- Pruebas nativas compartidas de las cinco operaciones y la demostración de escritura en los tres runtimes.
- Formularios y acciones CRUD dinámicos conectados de extremo a extremo al cliente Angular común.

**Advertencia:** que una proyección anuncie `operations: [LIST, GET, CREATE, UPDATE, DELETE]` no acredita que exista el
ejecutor de esas operaciones.

## 3. Primer caso candidato: `demo.items`

Aprovechar el ejemplo **ya existente** en `arp-contract`:

- **PostgreSQL (Java/.NET):** `items(id INTEGER PRIMARY KEY, code VARCHAR(12) NOT NULL, rating SMALLINT NOT NULL)`.
- **MariaDB (PHP):** `items(id INT PRIMARY KEY, code VARCHAR(12) NOT NULL, rating TINYINT SIGNED NOT NULL)`.
- **Data Dictionary:** `demo.itemCode` es texto de longitud `1..12`.
- **Logical Definition:** `demo.items` especializa `rating` con rango `0..10`, independiente del rango físico del motor.
- **Projection:** `demo.items.public` expone `id`, `code`, `rating` y declara las cinco operaciones;
  `demo.items.summary` deriva `id` y `code` y solo admite LIST/GET.
- **Identificación:** `id` suministrado expresamente en esta primera demo. La identidad generada automáticamente queda
  para un corte posterior, salvo decisión deliberada en el contrato.

### Secuencia demostrable

1. LIST inicial devuelve datos permitidos y paginados; GET recupera un artículo por su referencia o clave aprobada.
2. CREATE inserta `id=101, code='ART-101', rating=7` tras validación y autorización.
3. GET acredita la persistencia real y la precisión del valor.
4. UPDATE parcial cambia `rating` de `7` a `8` sin modificar `code`, con precondición válida y protección transaccional.
5. UPDATE con `rating=11` se rechaza por restricción lógica aunque el tipo físico pudiera almacenarlo.
6. UPDATE de un valor idéntico produce `changed=false` sin escritura efectiva cuando corresponda a la semántica
   aprobada.
7. UPDATE con una precondición obsoleta da conflicto sin sobrescribir datos concurrentes.
8. DELETE elimina exactamente el registro autorizado, con precondición de concurrencia acordada y sin eliminación masiva
   ni cascadas inesperadas.
9. GET posterior muestra ausencia y LIST no presenta el registro.
10. Una nueva columna física `internal_note` no se publica en proyecciones existentes por efecto de la introspección.
11. Una proyección solo de lectura y una autorización denegada impiden escribir incluso invocando la API directamente.
12. Una regla de validación **opcional** registrada por la demo ilustra cómo delegar una comprobación sin introducir
    lógica empresarial en ARP.

La demo no sustituye pruebas de límites, errores, colisiones, DDL externo, transacciones y seguridad.

## 4. Decisiones de contrato que hay que concretar antes de escribir

### A. Exposición y despacho

Acordar cómo se vinculan una Projection registrada, las operaciones que declara y el ejecutor gestionado o delegado.
Reutilizar el significado existente de `operations`: **declarar no significa autorizar ni ejecutar**. No exigir un YAML
de servicio independiente por cada CRUD si no aporta valor.

### B. CREATE

Definir campos permitidos, obligatorios, ausentes, `null`, valores predeterminados, clave explícita de esta demo,
unicidad, resultados y errores. El servidor no admite que el cliente escriba campos físicos no publicados ni confíe en
valores de identidad o tenant aportados sin validar.

### C. UPDATE parcial

Reutilizar lo ya propuesto en SERVICES-001/002: `changes` diferencia ausente de `null`; precondiciones por campo; se
conservan los cambios ajenos; un conflicto aborta toda la operación; comparación final y persistencia protegidas
atómicamente; no-op sin escritura; histórico inválido **omitido** no se reescribe ni se valida como si fuese nuevo.
Distinguir rollback demostrado de resultado de commit desconocido.

### D. DELETE

Cerrar expresamente precondición frente a modificaciones concurrentes, comportamiento de registro ausente, prohibición
de cascadas no declaradas, eliminación física frente a lógica y resultado observable. **No improvisar** la semántica de
DELETE como si estuviera cubierta por el contrato de UPDATE.

### E. Reglas de negocio y autoridad

El servidor comprueba exposición de campo, operación registrada y autorización confiable de la aplicación. Para las
reglas de código, prever extensión voluntaria en el punto de validación/operación; si existen efectos, validaciones
dependientes o auditoría obligatoria, la aplicación podrá exigir ejecución delegada y misma transacción. No crear una
librería universal de reglas ni un sistema RBAC propio.

### F. Alcance del primer proveedor

Demostrar escritura gestionada solo para capacidades físicas verificadas (tabla ordinaria, clave y campos soportados).
`incompatible` y `not verified` no son autorización para escribir; comportamientos que no se pueden garantizar se
rechazan de forma segura o se delegan.

## 5. Plan de ejecución y puertas de aceptación

### Tramo 0 — Congelación del diagnóstico

**Salida:** inventario trazable de clases, contratos, fixtures, demos y pruebas existentes; registrar qué se reutiliza y
qué falta. No renombrar paquetes históricos ni generar versiones. Mantener la documentación aprobada y las decisiones
nuevas separadas de hipótesis.

**Puerta:** alcance del caso `demo.items`, contrato preexistente y fronteras de responsabilidad identificados; no hay
dudas sobre qué componentes están ya implementados.

### Tramo 1 — Contrato neutral de escritura (`arp-contract`)

**Salida:** especificación y fixtures independientes del lenguaje para CREATE, UPDATE y DELETE gestionados, más
invocación/rechazo del delegado, autorización, validaciones, límites de transacción y errores. Mantener los fixtures
LIST/GET previos sin alteración injustificada.

**Puerta:** verificadores de contrato positivos y negativos verdes; decisiones CREATE y DELETE cerradas; no se crea un
nuevo formato innecesario; la especificación distingue destino, Projection, contexto confiable y operación.

### Tramo 2 — Primera implementación vertical PHP/MariaDB

**Salida:** adaptador de escritura acotado y reutilización del lector PHP/MariaDB existente; transacciones reales y
callbacks opcionales hacia la aplicación; demo PHP con cinco operaciones y trazabilidad de resultados. Esta
implementación se revisará primero por ser el lenguaje con el que el responsable del proyecto tiene mayor experiencia.

**Puerta:** pruebas reales de MariaDB de creación, lectura, actualización, eliminación, conflicto, rollback, ausencia,
exposición, denegaciones, DDL e histórico; ninguna operación de escritura se publica sin evidencia de garantías.

### Tramo 3 — Portabilidad posterior a Java/PostgreSQL y .NET/PostgreSQL

**Salida:** implementaciones Java y .NET independientes del mismo contrato, después de revisar y estabilizar el
incremento PHP, sin copiar lógica empresarial ni fixtures. Reutilización de proveedores y validadores existentes.

**Puerta:** mismos resultados contractuales para los tres runtimes; diferencias físicas declaradas; ninguna regresión de
LIST/GET ni de Data Dictionary; limpieza de recursos de pruebas sin afectar a otros proyectos. Los motores SQL
adicionales para escritura no bloquean el primer CRUD.

### Tramo 4 — Demo Angular común (primer CRUD completo)

**Salida:** listados, ficha, formulario de creación, edición parcial y eliminación conectados a los tres backends; se
aprovecha `angular-ui-runtime` donde proceda. API HTTP de demostración delgada y expresamente diferenciada del contrato
neutral.

**Puerta:** con un único cliente, se puede cambiar entre Java, .NET y PHP y repetir la misma secuencia CRUD. Campos y
botones visibles no sustituyen comprobaciones del servidor; las peticiones directas prohibidas también se rechazan. No
se muestra una operación que el backend no ofrece.

### Tramo 5 — Validación en aplicaciones reales (posterior al primer CRUD de demo)

**Salida:** analizar primero un caso ya implementado de una aplicación consumidora (una entidad sencilla), comparando
sus necesidades de autorización, persistencia y auditoría con el contrato ARP **sin sustituir de inmediato** Spring
Security, jOOQ, Flyway ni la auditoría. Contrastar después con un mantenimiento sencillo de otra aplicación consumidora
para comprobar que la abstracción no queda ligada a una aplicación consumidora. Elegir la primera integración real según
menor riesgo y beneficio comprobado, no por una obligación de arquitectura.

**Puerta:** ninguna pérdida funcional ni debilitamiento de seguridad/transacciones/auditoría; uso de ARP estrictamente
optativo. Un resultado desfavorable debe poder llevar a no integrar ARP en ese módulo.

## 6. Estrategia de pruebas para limitar el crecimiento

- **Contrato común:** fixtures de semántica reutilizados por Java, .NET y PHP.
- **Conformidad del runtime:** parser, validación, invocación y resultados; independientes del motor.
- **Adaptador por motor:** transacciones, SQL parametrizado, claves, errores del proveedor, restricciones y
  compatibilidad física.
- **Prueba end-to-end:** un pequeño conjunto representativo para cada backend usando el mismo cliente Angular; no
  multiplicar indiscriminadamente todas las pruebas funcionales por todos los motores.
- **Pruebas de regresión:** preservar el núcleo y LIST/GET, incluidas referencias opacas, políticas de fila,
  invalidación y límites.
- **Concurrencia real:** dos conexiones o hilos independientes, no solo simulación secuencial; verificar aislamiento,
  conflictos, no-op, rollback y estado de commit incierto.
- **Seguridad:** denegación de campos y operaciones, restricciones de filas, contexto/tenant confiable, protección
  frente a SQL arbitrario e inyección, cero filtración de columnas nuevas.

## 7. Qué NO entra en el primer CRUD

- Motor de reglas general, motor de workflows, colas, RBAC o autenticación de ARP.
- CRUD universal sobre vistas, joins, varias tablas o relaciones empresariales con efectos no triviales.
- Generación automática de toda la estructura física de cualquier aplicación.
- Migración histórica desde otra aplicación consumidora ni sustitución del código empresarial de una aplicación
  consumidora.
- Administración de tenants, caché distribuida, auditoría empresarial incorporada a ARP, importación/exportación masiva.
- Autoincrementos multibase, todas las variantes de SQL, todos los motores de escritura o todos los controles de UI.
- Publicación de versión/release/tag del producto ARP.

## 8. Criterio de «primer CRUD conseguido»

Un desarrollador define una entidad simple mediante los metadatos compartidos, publica una Projection explícita,
registra capacidades y restricciones en el servidor, inicia una demo de cualquiera de los tres runtimes y utiliza el
**mismo** cliente Angular para crear, consultar, modificar y eliminar registros reales; las reglas, permisos, errores y
concurrencia se cumplen en el servidor y las pruebas compartidas lo demuestran. Si no se cumplen todas estas
condiciones, existe un incremento parcial, pero no el primer CRUD completo.

## 9. Referencias existentes (no confundir con normas publicadas)

- [`arp-contract` — arquitectura](https://github.com/alxarafe/arp-contract/blob/main/docs/architecture.md)
- [Acuerdos originales
  D01–D11](https://github.com/alxarafe/arp-contract/blob/main/docs/decisions/ARP_CDS_modelo_semantico_primera_integracion_Angular.md)
  — **identificador histórico del archivo**, no nomenclatura nueva propuesta.
- [Diseño de modelos y proyecciones](https://github.com/alxarafe/arp-contract/blob/main/docs/features/arp-cds-001.md) —
  nombre histórico de archivo.
- [Lectura LIST/GET](https://github.com/alxarafe/arp-contract/blob/main/docs/features/arp-cds-listget-001.md) —
  candidato de contrato.
- [Servicios 001](https://github.com/alxarafe/arp-contract/blob/main/docs/features/arp-services-001.md) y [Servicios
  002](https://github.com/alxarafe/arp-contract/blob/main/docs/features/arp-services-002.md) — candidatos de contrato.
- [Demo Angular común](https://github.com/alxarafe/arp-contract/tree/main/demo/client/angular)
- [`arp-java`](https://github.com/alxarafe/arp-java), [`arp-dotnet`](https://github.com/alxarafe/arp-dotnet),
  [`arp-php`](https://github.com/alxarafe/arp-php)

## 10. Estado de las decisiones en este documento

**Ya acordado:** diseño optativo, capas Physical/Logical/Projection, CRUD gestionado simple y delegado para dominio,
contratos/fixtures primero, Java/.NET/PHP, un Angular, validación de servidor, no versions parciales.
**Ya acordado adicionalmente:** PHP/MariaDB es el primer runtime de escritura, por facilidad de revisión del responsable
del proyecto. **Recomendado para aprobación:** `demo.items` como primer escenario CRUD, límite de identidad suministrada
en demo, puertas por tramo y comparación con una aplicación consumidora y otra aplicación consumidora antes de fijar la
primera integración real.
**Pendiente de especificación técnica:** forma final de registro/ejecución, CREATE (null/defaults/identidad), DELETE
(concurrencia/ausencia/cascadas), integración de reglas y auditoría del anfitrión, forma concreta de las pruebas nativas
de escritura.