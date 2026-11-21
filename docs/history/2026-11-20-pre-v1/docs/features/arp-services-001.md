# ARP-SERVICES-001 — Semántica neutral de operaciones y cambios concurrentes

**Estado:** borrador de revisión; no es formato normativo, contrato de transporte publicado ni implementación de runtime.
**Fecha:** 2026-11-16.
**Base:** ARP-ARCH-001, decisiones D01–D11 de ARP-CDS-001, ARP-CDS-PHY-001 y acuerdo de edición histórica y concurrencia por campo.

## 1. Separación de responsabilidades

El modelo lógico aporta campos, tipos y restricciones. Una **proyección** delimita datos/campos expuestos. Un
**servicio/operación** establece qué acción puede ejecutarse y con qué comportamiento. Una **vista o formulario**
organiza la experiencia: pestañas, paneles, agrupaciones, controles y acciones. La **autorización** procede de la
aplicación anfitriona y restringe lo que puede ejecutarse o leerse, incluso cuando la operación o los campos
figuren en metadatos públicos.

**Cuestión deliberadamente abierta:** si cada CRUD se deriva de una proyección, se configura en una definición de servicio propia, o ambas opciones coexisten; y cómo se seleccionan proyecciones según contexto y roles. El campo candidato `operations` existente en `arp.projection/v1` **no se elimina ni redefine** en esta propuesta; su vínculo con un servicio ejecutable queda pendiente. No crear ahora un YAML obligatorio por CRUD ni introducir componentes visuales en el esquema de proyección.

Las operaciones `LIST`, `GET`, `CREATE`, `UPDATE` y `DELETE` son **capacidades funcionales neutrales**. `PATCH` es
una posible representación HTTP de `UPDATE` parcial, **no** una sexta capacidad ni una obligación de que ARP use
HTTP. El mismo comportamiento debe poder ejecutarse localmente, desde un adaptador HTTP o mediante un manejador
registrado por la aplicación.

## 2. Alcance de las operaciones

| Operación | Comportamiento mínimo previsto | Aspectos todavía abiertos |
| --- | --- | --- |
| `LIST` | Lectura limitada a los campos y registros efectivamente expuestos y autorizados | Filtros, paginación, ordenación y formato de respuesta |
| `GET` | Lectura de un registro según identidad y ámbito de acceso autorizados | Clave pública, representación y control de caché |
| `CREATE` | Alta con validación completa de los valores aportados y reglas de presencia/defaults | Sintaxis de defaults y required, generación de claves e idempotencia |
| `UPDATE` | **Actualización parcial** de campos solicitados; conflictos concurrentes por campo | Transporte HTTP exacto, tokens/revisiones, reintentos |
| `DELETE` | Borrado autorizado y coordinado con dependencias/transacciones | Borrado lógico/físico, concurrencia y políticas de dominio |

La primera ejecución **gestionada** de CRUD solo se considera para una tabla persistente con clave inequívoca y
capacidades comprobadas; otros casos usan manejadores delegados. Declarar una operación no concede permiso ni
asegura que sea gestionable. La aplicación conserva su lógica de negocio, sus transacciones y su elección de
persistencia.

## 3. Regla de UPDATE parcial

El cliente conserva una instantánea inicial y prepara un conjunto de **cambios** con los campos cuyos valores
finales aceptados difieren del original, con comparación tipada/canónica. Un campo ausente del conjunto no se
actualiza. `null` presente es una escritura explícita y está sujeto a nulabilidad y demás reglas.

El servidor valida **cada campo explícitamente incluido**, aunque su valor coincida con el almacenado, sin admitir
un valor histórico inválido como excepción para una nueva escritura. También valida las reglas dependientes que
resulten aplicables. No tiene obligación de revalidar individualmente todos los datos antiguos no modificados, pero
nunca puede saltarse invariantes de dominio afectadas. Si no hay cambios efectivos, no se emite una escritura SQL
ni un efecto de negocio por ese mero hecho.

**Alcance de escritura:** únicamente campos efectivos que requieren persistencia. Los campos no incluidos no aparecen en un `SET` SQL ni se sustituyen por copias antiguas. Una operación multicolumna debe ser **atómica**: no se escriben los campos aparentemente seguros si otro campo de esa misma petición está en conflicto o falla una regla. Esto tampoco equivale a permitir escrituras de campos fuera de la proyección o no autorizados.

## 4. Concurrencia optimista por campo

Para cada campo incluido, se conserva el **valor base** que recibió el cliente y se contrasta con el **valor
actual** justo antes de escribir. Si el actual difiere de la base, el servidor comunica conflicto en ese campo y
**no persiste ningún cambio de esa petición**. Un cambio en un campo distinto no produce por sí mismo conflicto,
pero sí puede activar un validador dependiente o una invariante que impida guardar.

El diagnóstico de conflicto, **solo si el usuario está autorizado a leer esos datos**, podrá presentar por campo
`original` (al abrir), `actual` (persistido) y `propuesto` (usuario). No hay sobrescritura automática. El cliente
permite conservar el actual o solicitar confirmación expresa para aplicar su propuesta.

Tras una confirmación, el servidor **vuelve a comparar atómicamente** el valor actual con el valor que el usuario
confirmó estar sobrescribiendo. Si ha vuelto a cambiar, devuelve un nuevo conflicto; nunca aplica una confirmación
obsoleta. La comparación y escritura requieren protección transaccional, bloqueo apropiado o compare-and-swap de
almacenamiento. Una lectura previa sin ese mecanismo no basta.

La propuesta de fixture utiliza `baseline` y `confirmedCurrent` para modelar las precondiciones de cada campo. Es
**notación de prueba**, no esquema de petición ni token de confirmación publicado. El backend no confiará en
permisos ni en identidad indicados por el cliente. Una confirmación no exime de autorización ni de validar los
valores y las reglas de negocio.

**Precisión sobre el alcance:** comparar valores detecta divergencia **actual** de un campo, no todos los episodios históricos de cambio. Si el valor pasa A→B→A, detectar ese episodio requiere revisión/versionado por campo u otra evidencia. La detección de ABA y la identidad/formato final de precondiciones quedan abiertos. Tampoco se impone un contador de versión global que rechace indiscriminadamente cambios en columnas diferentes.

## 5. Valores históricos y formularios

Con `rating` restringido a `0..10`, un `11` preexistente puede mostrarse y conservarse mientras `rating` no se
incluya en el cambio. Si el usuario edita ese control, la UI solo ofrece/acepta valores permitidos y no puede
volver a seleccionar `11` durante esa edición. Un `CREATE` tampoco lo acepta. El servidor valida el campo enviado
aunque el cliente se haya equivocado o se omitan controles de UI.

Este comportamiento no convierte una proyección en un formulario. La futura capa de presentación podrá usar
paneles, pestañas, secciones y controles opcionales. Se debe poder generar un formulario elemental sin exigir un
YAML visual por cada CRUD. Los metadatos de presentación no conceden acceso ni alteran los tipos/restricciones.

## 6. Orden de ejecución y errores

Como orientación funcional, el servidor verifica habilitación del recurso y operación, exposición y autorización
efectiva (incluida lectura de información para resolver conflictos), definición y forma de los cambios, validación
de campos, precondiciones de concurrencia, reglas dependientes y escritura atómica. El orden técnico definitivo
debe evitar filtraciones y carreras de concurrencia; no se afirma que un simple listado fijo sea suficiente.

Se conservan las cinco familias de error de ARP-CDS-001: definición inválida, incompatibilidad física, dato
inválido, operación prohibida y error de ejecución. **Conflicto concurrente** es un resultado funcional específico
que aún necesita ubicación/código formal en el futuro contrato de resultados; no debe esconderse como
`execution-failure` indistinguible ni provocar una sobrescritura.

La respuesta de conflicto no puede revelar campos no expuestos, valores ocultos, identidades de otros usuarios ni
registros inaccesibles. Si no hay autorización de lectura suficiente, la aplicación debe devolver un rechazo
seguro, no inventar valores ni ofrecer confirmación de un valor que no puede mostrar.

## 7. Evidencia candidata y límites

- `fixtures/services/v1/cases.json` contiene escenarios **sintéticos** de actualizaciones parciales, conflictos,
  confirmación, datos históricos y autorizaciones.
- `tools/check_services_draft.py` comprueba esos escenarios usando un pequeño oráculo en memoria, sin BD real,
  autorización real ni motor de reglas.
- `tests/test_services_draft.py` protege decisiones representativas y verifica que ninguna ejecución de ejemplo
  altere sus entradas.

**No está definido ni aprobado aún:** la gramática final de un documento de servicio, su posible correspondencia con una proyección, la estructura de los formularios, roles, endpoints HTTP, serialización completa, identidad/versión de precondiciones, protocolo de concurrencia de `DELETE`, ejecución asíncrona, transacciones entre varias entidades, ACL de filtros y conexiones de datos. No hay cambios de runtime, API pública ni versión de ARP.

## 8. Próximo corte de decisión

Revisar este contrato funcional y aprobar, corregir o dejar pendientes sus puntos explícitos. Después formalizar
**la forma neutral de invocar un servicio** y sus resultados, sin decidir todavía si una proyección genera
automáticamente su CRUD ni vincular un servicio a pestañas/paneles. La integración Java/.NET/PHP y las pruebas
transaccionales con PostgreSQL/MariaDB solo proceden tras aprobar el contrato de ejecución correspondiente.