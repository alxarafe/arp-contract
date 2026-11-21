# ARP-CRUD-001A — Contrato neutral de escritura

**Estado:** candidato para revisión; no aprobado como formato normativo, publicado ni implementado en runtimes.
**Base:** `95d72dcd9c9e4ba7fc78efa4150224fa1d61ff5d`, `main` actualizado el 21/11/2026.
**Alcance:** CREATE, DELETE y su enlace con UPDATE parcial sobre `demo.items`; sin endpoints ni cliente visual.

## 1. Acuerdos, propuestas y pendientes

Se conservan las fronteras de [arquitectura](../architecture.md), las
[decisiones D01–D11](../decisions/ARP_CDS_modelo_semantico_primera_integracion_Angular.md),
[Physical/Logical/Projection](arp-cds-001.md),
[SERVICES-001](arp-services-001.md), [SERVICES-002](arp-services-002.md),
[LIST/GET](arp-cds-listget-001.md) y [compatibilidad histórica](arp-cds-001-compatibility-and-historical-data.md).
Sus textos completos y estados originales están conservados en el archivo documental enlazado desde esas rutas.
La incorporación de un borrador a `main` no constituye publicación ni prueba de capacidad de un runtime.

**Acuerdos preservados:** adopción optativa, dominio y permisos de la aplicación, neutralidad de lenguaje y motor,
proyección explícita, contexto confiable separado, escritura simple gestionada o ejecución delegada, contrato y
fixtures antes de runtimes. No se alteran las garantías de UPDATE ni las expectativas de sus vectores existentes.

**Propuesto en este candidato:** enlace mínimo de registro y proyección, presencia y defaults para CREATE,
identidad explícita, eliminación física con evidencia del estado leído, resultados y códigos de este perfil.
Las palabras de obligación de este documento expresan el comportamiento a revisar, no una aprobación implícita.

**No aprobado por este trabajo:** `INTEGER`, tipos directos, autoridad `CDS`/`DATABASE`, creación de tablas,
los cinco estados nuevos de compatibilidad física ni los demás puntos del
[borrador 1.0](../contract-v1-draft.md). Véase la [revisión de compatibilidad](../review-contract-v1.md).
Se usan los identificadores escalares históricos vigentes y las definiciones actuales de la demo, sin alias nuevos.

## 2. Registro y cinco operaciones

El registro confiable de la aplicación enlaza **destino → Projection activa → Logical Definition → proveedor**.
Se reutiliza el enlace de LIST/GET; no se deduce de nombres físicos ni se exige un servicio o YAML por cada CRUD.
Cada operación requiere simultáneamente declaración en la Projection, habilitación en el registro, autorización
actual y capacidad demostrada del ejecutor. `operations` mantiene su gramática y significado actuales.

El registro puede elegir un ejecutor gestionado o un manejador delegado para una operación concreta.
No se cambia de uno a otro automáticamente al fallar una capacidad, validación o transacción.
Una aplicación puede usar solo lectura, solo el Data Dictionary o sus propios servicios especializados.
La disponibilidad en menús o metadatos de cliente nunca acredita autorización del backend.

Se reutilizan sin editar:

- [Data Dictionary](../../examples/demo/cds/dictionary.yaml) y
  [Logical Definition](../../examples/demo/cds/logical.yaml).
- [Projection pública](../../examples/demo/cds/public.yaml): `id`, `code`, `rating`, cinco operaciones declaradas.
- [Projection derivada](../../examples/demo/cds/summary.yaml): `id`, `code`, únicamente LIST y GET.
- [SQL MariaDB](../../examples/demo/sql/mariadb.sql) y [SQL PostgreSQL](../../examples/demo/sql/postgresql.sql).
- [Manifiesto de definiciones y observaciones ilustrativas](../../fixtures/cds/v1/manifest.json).

Las observaciones no acreditan el esquema de una base real. Cada adaptador debe observarlo y demostrar sus
capacidades: tabla persistente única, PK inequívoca, nulabilidad, codec exacto, restricciones e identidad verificadas.
Se exige un límite atómico que cubra políticas, reglas dependientes, precondiciones y persistencia.
Una vista, múltiples tablas, tipos no soportados o capacidades no verificadas no reciben escritura gestionada.
Triggers, cascadas y efectos auxiliares no caracterizados impiden ofrecerla. El primer perfil no admite efectos
sobre otras filas, aunque una cascada ya exista: no crea ni activa cascadas nuevas ni las presume seguras.

## 3. Invocación, contexto e identidad

Se conserva `invocar(petición, contexto confiable)` de SERVICES-002 como separación conceptual, sin firma impuesta.
La petición contiene exactamente `target`, `operation`, `inputs`; no contiene permisos, ámbito confiable, nombres
SQL, rutas ejecutables ni selectores de proyección libres. Ausente o nulo no equivale a `inputs: {}`.
La aplicación pública puede carecer de principal; sigue aplicando exposición, restricciones y validación.

CREATE candidato:

```json
{"target":"demo.items","operation":"CREATE","inputs":{"values":{"id":"8","code":"A-008","rating":"5"}}}
```

UPDATE conserva `changes`, `baseline` y la capacidad opcional de `confirmation` de SERVICES-002; su `key` se
resuelve con la misma identidad tipada que LIST/GET. No se cambia la semántica de la confirmación ni se publica
una sintaxis de token definitiva. El adaptador interno del oráculo traduce solo la identidad de la demo al arnés
histórico de SERVICES-002, manteniendo la vinculación de su evidencia; no modifica los fixtures originales.

DELETE candidato:

```json
{
  "target": "demo.items",
  "operation": "DELETE",
  "inputs": {
    "key": {"components": [{"field": "id", "type": "INT32", "value": "7"}]},
    "precondition": {"reference": "evidencia-opaca-del-estado-leido"}
  }
}
```

La clave pública reutiliza LIST/GET: componentes completos, orden PK, nombre y tipo efectivos, valores exactos.
La primera demo utiliza `id: INT32` explícito, sin autoincrementos, secuencias ni generación implícita.
CREATE exige que el solicitante pueda aportar `id`; no lo sustituye un default. UPDATE no cambia la PK en este corte.
El resultado CREATE devuelve exclusivamente la identidad segura; no devuelve la fila ni columnas auxiliares.

Si la PK no puede leerse, la aplicación requiere una referencia opaca con vinculación al propósito de escritura,
destino, proyección, identidad completa, contexto, revisión de acceso y generación. Conocer la PK no da permiso.
Una referencia de propósito GET no se reutiliza directamente para UPDATE o DELETE. La forma de obtener evidencia
para escritura es una capacidad explícita del anfitrión tras una lectura autorizada; no se amplía silenciosamente
la salida vigente de GET. El oráculo prueba ese mecanismo con referencias privadas preestablecidas.
CREATE gestionado con PK oculta no está habilitado por este perfil de identidad explícita.

## 4. CREATE: presencia y validación

`inputs` contiene solo `values`, un mapa de campos aportados. Se rechaza todo campo desconocido, no expuesto o
no escribible con autorización efectiva, incluso si existe físicamente. No se admiten escrituras por asignación
masiva desde nombres físicos ni ampliaciones automáticas de la Projection tras una nueva columna.

Para cada campo persistente del perfil:

| Entrada | Tratamiento propuesto |
| --- | --- |
| Valor presente | Validar tipo, restricciones y autorización; normalizar sin pérdida. |
| `null` presente | Es nulo explícito; requiere nulabilidad comprobada, nunca activa un default. |
| Ausente con default verificado | Usar el default comprobado y validar su valor efectivo. |
| Ausente nullable sin default | Representa nulo según la nulabilidad física demostrada. |
| Ausente no nullable sin default | Rechazar por valor requerido. |
| PK ausente | Rechazar; no se inventa generación ni default de identidad. |

El esquema de autoría de defaults y presencia lógica sigue pendiente. Este perfil usa evidencia confiable del
proveedor o registro, no añade propiedades al diccionario, Logical Definition ni Projection. Los defaults de la
demo real no existen: sus tres columnas son obligatorias. Las variantes nullable/default de los fixtures son
supuestos sintéticos identificados en `host`, no cambios en los ejemplos. Un default desconocido, volátil o con
efectos no demostrados no se utiliza para justificar escritura gestionada. Si se omite una columna física oculta,
el proveedor debe acreditar que puede satisfacerla sin aceptar datos privados aportados por el solicitante.

Validar antes de persistir: Data Dictionary, restricciones del modelo lógico efectivo y dominio físico comprobado;
la base puede todavía rechazar unicidad, integridad u otras restricciones al insertar. La autorización y las
invariantes que dependan del estado deben seguir vigentes dentro del límite atómico, también frente a carreras.
En la demo `code` admite longitud 1..12 y `rating` admite 0..10; el tipo físico más amplio no amplía esa validación.
Una restricción actual no se elude por existir registros históricos con otro valor.

La verificación del dominio completo sigue las reglas de compatibilidad existentes. No se adopta la propuesta
1.0 de permitir una definición incompatible escribiendo solo su intersección física. Un proveedor no verificado
falla por capacidad no disponible; una incompatibilidad demostrada conserva su familia específica.

La PK duplicada y los rechazos de integridad dan un diagnóstico genérico `CONSTRAINT_REJECTED`, sin SQL ni identidad
de la fila que impide insertar. Así una colisión no confirma la existencia de una fila fuera del ámbito autorizado.
No hay overwrite, upsert ni reintento automático. La unicidad debe imponerse en almacenamiento, sin depender de
una consulta previa susceptible a carreras. Un rechazo de almacenamiento solo afirma ausencia de efectos si se
acredita reversión completa; en caso contrario se informa resultado incierto.

## 5. DELETE: estado leído y concurrencia

Se propone **borrado físico** de exactamente una fila autorizada. Soft delete y cambios de estado pertenecen a
operaciones propias o delegadas, sin reinterpretar DELETE gestionado. No se implementa borrado masivo.

La PK por sí sola no es precondición suficiente. El anfitrión vincula la evidencia a una lectura autorizada y al
estado persistente relevante observado en ella, incluida la identidad completa. La evidencia tiene que cubrir
exactamente todos los campos no PK relevantes del perfil, además de destino, operación DELETE, Projection,
contexto/principal cuando exista, generación y revisión de acceso. En la demo son `code` y `rating`.
La evidencia opaca no concede autorización ni expone su contenido; puede ser un registro privado o protección
equivalente de la aplicación. El cliente no puede fabricar un `baseline` ni marcar un booleano como autoridad.

Antes de borrar se revalidan la vinculación, vigencia, autorización de fila y capacidades, y se compara el estado
actual con el leído **indivisiblemente con el borrado**. Una lectura seguida de DELETE sin protección no cumple.
Una diferencia en cualquier campo relevante produce `conflict` sin borrar nada. No se acepta confirmación ciega
para saltar una precondición DELETE obsoleta: se necesita nueva lectura y nueva evidencia válida.
No se usa la concurrencia por campo de UPDATE para omitir cambios en otros campos al eliminar toda la fila.

Los valores se comparan tipados, con nulo explícito distinto de ausencia, sin revalidar como escritura un histórico
fuera del rango lógico. Por ejemplo `rating=11` puede formar parte de la instantánea DELETE si es físicamente
representable y no cambió. Una columna nueva obliga a acreditar la cobertura de estado antes de ofrecer DELETE;
no entra en la proyección por ese motivo. Campos ocultos pueden compararse internamente solo con capacidad y
evidencia suficientes; nunca se devuelven en el conflicto. Si falta cobertura, codec o capacidad, se rechaza.
No se permite ignorar una columna persistente por no aparecer en la Projection.

Comparar estado detecta divergencia actual, **no episodios ABA**. No se afirma detectar A→B→A ni sustitución por
otra fila con la misma identidad y el mismo estado. Si la aplicación exige esa garantía debe aportar una revisión
de registro/incarnación o delegar; la demo de comparación por valor no acredita esa detección histórica.
Esto conserva el límite ya expuesto para UPDATE y evita inventar un contador global obligatorio.

Con operación autorizada, identidad y evidencia válidas, fila ausente e inaccesible producen el mismo éxito
`deleted:false`, sin distinguir la causa ni afirmar que la fila exista. Evidencia desconocida, caducada, fuera
de ámbito o de propósito GET se rechaza sin revelar existencia. Una revocación global de operación da `UNAVAILABLE`.
Una relación que impide eliminar da rechazo genérico de integridad, sin nombres privados de tablas o filas.
No se ejecutan nuevas cascadas para conseguir que el borrado pase.

## 6. UPDATE parcial y reglas opcionales

Se reutilizan SERVICES-001/002: ausencia no escribe, nulo explícito requiere nulabilidad, cada campo incluido se
valida aunque no cambie, históricos omitidos se conservan, conflictos se comparan por campo y los cambios
independientes no se sobrescriben. Un conflicto invalida toda la petición. Se revalida la confirmación contra el
estado confirmado más reciente y la vinculación de propuesta y contexto. No-op produce `changed:false`, sin
escritura ni efecto de negocio por guardar, manteniendo controles de autorización, reglas y precondiciones.
No se aplican defaults de CREATE a campos omitidos en UPDATE.

El arnés nuevo enlaza con el oráculo de SERVICES-002; los 25 vectores de SERVICES-001 y los 51 de SERVICES-002
se referencian por identificador y hash, sin duplicarlos ni alterar expectativas. Incluyen conflicto multicolumna,
confirmación vigente/obsoleta, rollback conocido, pérdida de permisos y resultado delegado incierto.
El resolver de campos físicos/lógicos y el codec entero de LIST/GET se reutilizan sin ampliar su perfil de lectura
para ejecutar escritura; la comprobación de proyecciones completas usa el resolver previo de la demo.

La aplicación puede registrar un **puerto opcional de evaluación**, sin lenguaje de reglas ni bibliotecas impuestas.
Recibe datos lógicos autorizados necesarios para la regla, operación, estado actual/candidato o eliminación,
campos afectados y contexto confiable separado. Devuelve permitir o rechazar con diagnóstico seguro aprobado.
No se exige organización física, clase o carpeta. El puerto no modifica el payload, persiste ni introduce efectos
externos bajo las garantías del perfil gestionado. Reglas con efectos u orquestación propia se delegan.
Si una regla requerida no puede evaluarse o proteger sus dependencias contra cambios concurrentes, no se escribe.
La aplicación conserva el contenido empresarial y decide qué invariantes dependen incluso de campos omitidos.

Un manejador delegado registrado puede ofrecer una operación especializada con su contrato de entrada/salida.
No hereda atomicidad, concurrencia, ausencia de efectos ni rollback del perfil gestionado por compartir despacho.
Exposición, validación del contrato registrado, autorización y filtrado de salida siguen siendo obligatorios.
Un delegado que afirme ofrecer este mismo perfil debe demostrar sus garantías. El ejemplo de delegado DELETE del
arnés acepta una clave y devuelve una salida preaprobada; no finge cumplir DELETE físico gestionado.

## 7. Resultados, fallos y seguridad de publicación

Se conservan los cuatro estados y cinco familias de SERVICES-002. No se añade un estado `unknown` ni se altera
el resultado de lecturas o de UPDATE. La salida aparece únicamente en éxito.

| Resultado | Salida o diagnóstico candidato |
| --- | --- |
| CREATE confirmado | `success`, `output:{created:true,key:...}`; solo identidad autorizada. |
| UPDATE confirmado | `success`, `output:{changed:true/false}` según SERVICES-002. |
| DELETE confirmado | `success`, `output:{deleted:true}`. |
| DELETE ausente/inaccesible | `success`, `output:{deleted:false}` con evidencia válida. |
| Divergencia DELETE | `conflict`, `conflictCode:CONCURRENT_CHANGE`, sin detalles de campos. |
| Controles o datos inválidos | `rejected`, sin salida; sin efectos del perfil gestionado. |
| Error técnico | `failed`, sin salida exitosa; no implica por sí mismo rollback. |

Los siguientes códigos son propuestas locales del perfil, sin renombrar los códigos existentes de UPDATE:

| Familia | Códigos propuestos |
| --- | --- |
| `definition-invalid` | `INVALID_DEFINITION` |
| `physical-incompatible` | `INCOMPATIBLE_STORAGE` |
| `invalid-data` | `INPUT_SHAPE`, `INVALID_KEY`, `REQUIRED_VALUE`, `INVALID_VALUE` |
| `invalid-data` | `PRECONDITION_REQUIRED`, `CONSTRAINT_REJECTED`, `BUSINESS_REJECTED` |
| `operation-not-allowed` | `UNAVAILABLE`, `CAPABILITY_UNAVAILABLE`, `GENERATION_EXPIRED` |
| `execution-failure` | `ROW_IDENTITY_INVALID`, `ROW_DECODE_FAILED`, `PERSISTENCE_FAILED` |
| `execution-failure` | `COMMIT_FAILED`, `OUTCOME_UNKNOWN`, `RESPONSE_UNAVAILABLE`, `HANDLER_FAILED` |

Un fallo de persistencia anterior al commit produce `PERSISTENCE_FAILED` solo con evidencia de reversión;
`COMMIT_FAILED` modela commit fallido y rollback completo acreditado. Si no puede probarse la reversión o se
pierde la certeza de commit/respuesta se usa `OUTCOME_UNKNOWN`: puede haber persistencia o no, sin éxito parcial.
La respuesta no ofrece `changed:false`, identidad creada ni promesa de reintento seguro en esos casos.
La instrumentación privada distingue los efectos reales simulados; no forma parte de la respuesta pública.

La pérdida de permisos, ámbito o generación antes del límite atómico impide escribir. Tras un commit confirmado,
se filtra también la publicación: si ya no se puede publicar una respuesta autorizada, se devuelve `failed` con
`RESPONSE_UNAVAILABLE`, sin la salida ni afirmación de rollback. El commit puede haber ocurrido; el adaptador debe
conservar esa evidencia. Un cambio de permisos después del commit no deshace retrospectivamente el almacenamiento.
No se afirma coordinación perfecta con revocaciones externas sin un mecanismo real que la demuestre.

Los mensajes no incluyen SQL, trazas, conexiones, filas ajenas, campos ocultos, valores de precondiciones opacas,
referencias privadas ni estado del arnés. No se promete igualdad temporal de errores. El formato definitivo de
certeza, localización, reintentos e idempotencia sigue pendiente, sin debilitar estas distinciones.

## 8. Matriz de evidencias y pruebas

[Manifiesto](../../fixtures/crud/write/v1/manifest.json), [vectores](../../fixtures/crud/write/v1/cases.json),
[codec](../../fixtures/crud/write/v1/codec-cases.json),
[oráculo](../../tools/check_crud_write_draft.py) y [regresiones](../../tests/test_crud_write_draft.py).
Las expectativas se almacenan explícitamente y se prepararon independientemente del resultado del oráculo.
`host`, defaults del arnés, overrides físicos, filas en el límite y observaciones son evidencia privada sintética,
no un YAML CRUD, permisos del cliente ni una API pública de configuración.

| Cobertura | Evidencia del oráculo | Demostración posterior requerida |
| --- | --- | --- |
| CREATE válido, identidad explícita | `create-valid`, `create-postgresql` | Inserción y lectura real. |
| Presencia y defaults | `create-required-*`, `create-null-*`, `create-verified-default` | Nulabilidad/default real. |
| Tipos y restricciones | `create-rating-range`, `create-id-overflow`, `create-code-too-long` | Codec y rechazo SQL. |
| Duplicados e integridad | `create-duplicate-key`, `delete-relation-restricts` | PK/FK concurrentes. |
| Campos y operaciones | `create-hidden-field`, `create-summary-readonly` | Restricciones del servidor. |
| Revocación | `create-field-permission-revoked`, `delete-permissions-revoked` | Intercalados de permisos. |
| UPDATE parcial/históricos | `update-demo-*` y 76 vectores SERVICES referenciados | SQL parcial, dos conexiones. |
| DELETE ligado a lectura | `delete-no-precondition`, `delete-get-purpose-not-delete` | Evidencia no falsificable. |
| Estado y conflicto | `delete-concurrent-change`, `delete-hidden-concurrent-change` | Compare/delete indivisible. |
| Ausencia e inaccesibilidad | `delete-absent`, `delete-inaccessible` | Sin filtración de filas. |
| Capacidad | `delete-unverified`, `delete-view`, `delete-cascades-unavailable` | Observación real del motor. |
| Fallos y commit incierto | `*-commit-rollback`, `*-uncertain-*` | Fallos de conexión y rollback. |
| Delegación | `delegated-*` | Contrato y garantías del manejador. |
| Codec | 11 casos JSON, exactitud >53 bits, nulo, Unicode, duplicados | Drivers sin float ni pérdida. |

El [inventario de obligaciones nativas](../../fixtures/crud/write/v1/provider-obligations.json) enlaza casos
con evidencias exigibles y declara `executed:false`. Hay 110 casos nuevos de escritura, 11 de codec y 76 casos
históricos referenciados. Las variantes PostgreSQL solo usan sus observaciones ilustrativas, sin conexión real.
La primera implementación será PHP/MariaDB, después Java/PostgreSQL y .NET/PostgreSQL, con los mismos vectores.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_crud_write_draft.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_documentation.py
git diff --check
```

El oráculo es finito y en memoria. No demuestra transacciones, bloqueos, aislamiento, protección criptográfica,
introspección, coordinación DDL, autorización real ni conformidad de runtimes. Deben probarse en MariaDB aislada
con conexiones independientes, no inferirse de `rowsAtBoundary` o de un booleano de capacidad del arnés.
No se requieren dependencias generales nuevas; se aplica `.editorconfig` y se conserva el formato de los archivos
existentes. No se modifican los ejemplos, esquemas de autoría, fixtures históricos, runtimes ni código de cliente.

## 9. Decisiones necesarias y asuntos pendientes

Se proponen expresamente para cerrar este corte, sujetos a revisión:

1. Enlazar las cinco operaciones con el registro y Projection activos sin un servicio obligatorio por CRUD.
2. Requerir PK explícita y pública para CREATE gestionado; identidad generada queda fuera de este perfil.
3. Usar eliminación física y evidencia opaca vinculada a lectura, con comparación completa y atómica del estado.
4. Igualar ausencia e inaccesibilidad de fila en DELETE con evidencia válida, sin revelar conflictos ocultos.
5. Mantener estados/familias y distinguir rollback acreditado, resultado incierto y salida no publicable tras commit.
6. Permitir evaluación opcional pura y delegación explícita, sin atribuir garantías no demostradas.

Pendientes de decisión o evidencia antes de implementar/afirmar conformidad:

- Aprobación de este candidato, nombres finales y representación de entradas/resultados; no es transporte HTTP.
- Emisión protegida, almacenamiento, caducidad, revocación y entrega de evidencias de escritura por cada anfitrión.
- Si se requiere detectar ABA o recreación de fila, revisión adicional y evidencia del proveedor; no se presume.
- Sintaxis futura de defaults/presencia lógica, identidades generadas, claves de otros tipos y otras tablas.
- Mecanismo real de protección de políticas y reglas dependientes dentro de las transacciones de cada adaptador.
- Pruebas de restricciones, cascadas, triggers, aislamiento y rollback/commit incierto en PHP/MariaDB.
- Metadatos públicos definitivos de certeza, reconciliación e idempotencia; ningún fallo habilita reintento ciego.
- Adopción independiente posterior por otros runtimes. `INTEGER` permanece pendiente y aislado.

No se implementan formularios, workflows ni motores de reglas; no se fusiona automáticamente ni se publica versión.

## 10. Resultado de la validación local

- **206 pruebas Python correctas**: 187 previas y 19 regresiones nuevas.
- **110 vectores de escritura y 11 de codec correctos**, más los **76 vectores SERVICES referenciados**.
- Los nueve verificadores contractuales previos, el nuevo oráculo y la comprobación documental: **PASS**.
- **237 referencias locales/Git** y los hashes de **25 documentos históricos** comprobados.
- `git diff --check`: correcto; UTF-8, LF, sangría y longitud de los nuevos archivos comprobados.
- Sin cambios en esquemas vigentes, ejemplos, fixtures históricos, propuesta INTEGER ni código de cliente.
- Sin ejecución de bases de datos ni conformidad nativa; las obligaciones de proveedores siguen sin ejecutar.