# ARP — Modelo semántico (CDS) y primera integración con Angular

**Fecha de consolidación:** 15 de noviembre de 2026
**Estado:** Acuerdos funcionales cerrados para iniciar su especificación contractual e implementación; los detalles técnicos identificados como pendientes no se presuponen aprobados.
**Documento rector de visión:** [`ARP_reorientacion_arquitectura_funcional.md`](./ARP_reorientacion_arquitectura_funcional.md).
**Relación con los contratos:** `arp-contract` será la fuente normativa de los nuevos formatos, semánticas y pruebas una vez especificados y aprobados; este documento recoge **decisiones de producto**, no publica por sí solo un contrato de ejecución.
**Versionado:** No se declara `v0.1`, no se publica versión y no se considera terminado el MVP global.

## 1. Propósito y alcance del tramo

ARP es una **plataforma agnóstica de los dominios empresariales** que ofrece mecanismos reutilizables para desarrollar aplicaciones. No incorpora entidades ni reglas de un ERP particular. Este documento concreta el **primer tramo vertical**, desde el diccionario existente hasta la representación y las operaciones de una proyección en Angular:

```text
                  Diccionario ARP existente
                  (tipos/restricciones)
                            │
BD real ──> Definiciones físicas generadas y regenerables
                            │
                            ▼
             Modelo lógico efectivo / CDS básico
              = físico + especializaciones YAML
                            │
                            ▼
               Proyecciones públicas explícitas
             (incluidas proyecciones derivadas)
                            │
                            ▼
            Servicios y operaciones declaradas
        CRUD automático simple o ejecución delegada
                            │
                            ▼
                Cliente Angular genérico
             listados, formularios y acciones
```

La cadena describe **este escenario de adopción basado en una base de datos**, no una obligación de usar SQL, CRUD o Angular en cualquier aplicación que consuma ARP. Los restantes bloques de la reorientación se definirán en su parte básica antes de establecer una versión global; luego se ampliarán y perfeccionarán hasta lograr un MVP viable.

## 2. Registro de decisiones aceptadas

Los siguientes once puntos se trataron de forma sucesiva y el usuario los confirmó. Este registro es la referencia operativa del tramo para impedir que decisiones posteriores reabran silenciosamente lo ya acordado.

| ID | Punto cerrado | Decisión |
|---|---|---|
| **D01** | Formatos y capas del modelo | YAML como autoría declarativa principal; JSON equivalente; modelo semántico neutral. Modelo físico autogenerado, lógica persistente y proyecciones públicas. APIs tipadas de autoría **opcionales y aplazadas**. |
| **D02** | CRUD y proyecciones | Las proyecciones pueden declarar LIST, GET, CREATE, UPDATE y DELETE. Ejecución **automática** para casos admisibles y **delegada** para comportamientos específicos. |
| **D03** | Alcance del CRUD automático | Primera implementación limitada a operaciones simples sobre **una tabla con clave identificadora**. Consultas mediante relaciones y escrituras complejas se ampliarán progresivamente; escrituras no automatizables se delegan. |
| **D04** | Ciclo de vida físico | **Generación bajo demanda** si falta la definición física; **invalidación explícita** después de cambiar el esquema; regeneración en el siguiente uso. No se exige sondeo continuo ni exploración completa al inicio. |
| **D05** | Interfaz Angular | Toda proyección pública puede suministrar metadatos para listados, formularios y acciones básicas; personalización declarativa opcional. Reutilización de `angular-ui-runtime`. |
| **D06** | Seguridad | Autenticación y autorización **opcionales**: se delegan en la aplicación anfitriona cuando existen. Sin identidad/permisos para aplicaciones realmente públicas; nunca se ignoran restricciones de exposición o validaciones del servidor. |
| **D07** | Validación y extensión | ARP ejecuta validaciones declarativas del diccionario y del modelo lógico; permite conectar validadores de la aplicación. Motor de reglas avanzado y otras integraciones se desarrollan después. |
| **D08** | Errores | Diagnósticos y resultados normalizados, equivalentes entre PHP, Java y .NET; distinguen definiciones, compatibilidad física, datos, operación y ejecución. |
| **D09** | Demos y conformidad | Demo autónoma en cada `arp-*`; definiciones y casos de prueba compartidos en `arp-contract`; **un solo cliente Angular** para los tres backends. Demos y pruebas de conformidad tienen funciones diferentes. |
| **D10** | Bases de datos de las demos | **Java: PostgreSQL; .NET: PostgreSQL; PHP: MariaDB.** El contrato lógico común no depende del motor. |
| **D11** | Orden de desarrollo | **Primero `arp-contract`**, después runtimes, demos y finalmente integración Angular; verificar cada tramo antes de pasar al siguiente; no publicar versiones parciales por rutina. |

Los acuerdos previos sobre los que descansan estas decisiones también quedan conservados expresamente en los apartados siguientes.

## 3. Modelo físico: descripción regenerable del almacenamiento

### 3.1. Qué se obtiene

- ARP puede generar **un archivo YAML físico por tabla o vista** existente de la base de datos, cuando esa definición se solicita y aún no existe.
- Describe únicamente hechos comprobables: nombre del objeto, columnas, tipos, longitudes/rangos/capacidades físicas, nulabilidad, claves, índices y relaciones que el proveedor pueda determinar de forma fiable.
- **La base de datos real es la autoridad** sobre su estructura; el YAML es un artefacto generado, prescindible y **no editable por el desarrollador**.
- La generación no atribuye significado empresarial a las columnas. Una columna `VARCHAR(10)` no se identifica automáticamente como `customer.code` por su nombre.
- Ejemplo: para `TINYINT SIGNED` el adaptador puede reconocer el rango físico de **−128 a 127**; no lo confunde con una restricción funcional de la aplicación.

### 3.2. Generación, invalidación y cambios de esquema (D04)

1. Cuando se requiere un objeto físico, ARP utiliza su definición si existe y sigue siendo válida según el procedimiento de invalidación acordado; si falta, **la genera bajo demanda** desde la base de datos.
2. Tras una modificación de estructura mediante un proceso controlado, el responsable de la migración **invalida** la definición física correspondiente (puede eliminar el YAML generado).
3. La invalidación afecta también a **catálogos lógicos efectivos, proyecciones compiladas y cachés dependientes**, no solo al fichero físico.
4. El siguiente acceso reconstruye la definición y vuelve a validar las dependencias.
5. Si desapareció una columna o cambió una capacidad, ARP **no elimina ni corrige silenciosamente** los YAML del desarrollador: informa de la incompatibilidad y no utiliza el recurso afectado de manera insegura.
6. Para cambios efectuados fuera de las migraciones controladas debe existir una **invalidación explícita/manual**; no se afirma que ARP pueda detectar por sí solo cualquier DDL externo.

No se requiere vigilar constantemente la base de datos ni reconstruir el catálogo completo al arrancar. La reconstrucción debe evitar exponer versiones incompletas; los detalles de concurrencia/atomicidad se especificarán en el contrato técnico.

### 3.3. Módulos desactivados

- El catálogo físico puede seguir reflejando las tablas que **realmente continúan en la base de datos**, aunque pertenezcan a un módulo desactivado.
- Desactivar un módulo **no elimina** sus tablas, sus YAML lógicos, sus proyecciones ni sus reglas.
- Las definiciones de un módulo desactivado dejan de integrar el **catálogo lógico público activo**; sus servicios no se exponen.
- Al reactivarlo, ARP vuelve a construir y comprobar sus definiciones y dependencias.
- La pertenencia de una tabla a un módulo la declara la **aplicación anfitriona**; no se deduce exclusivamente del nombre de la tabla.

## 4. Modelo lógico: físico + especializaciones persistentes (D01)

**Modelo lógico efectivo = descripción física actual + especializaciones declarativas del consumidor.**

- El desarrollador mantiene YAML propios, separados de los artefactos físicos generados.
- Una definición lógica puede vincular un campo al **elemento del diccionario** que le corresponde (`customer.code`), añadir restricciones contextuales más estrictas, etiquetas, descripciones, hints, literales y otros metadatos semánticos aplicables.
- Las restricciones lógicas deben ser compatibles tanto con los **límites físicos demostrados** como con las restricciones intrínsecas del diccionario; no se debilitan ni contradicen silenciosamente.
- El sistema reutiliza `ARP-DICT-001` para los tipos y restricciones escalares ya definidos; **no duplica** ese diccionario en CDS.
- Si se incorpora una columna nueva al esquema físico, **aparece automáticamente** en el modelo lógico efectivo aunque el YAML lógico no la mencione. No se reescribe el YAML del usuario.
- Si una columna se elimina o se estrecha y una especialización deja de ser válida, esta se **conserva** para que el desarrollador pueda corregirla. No se pierde al desactivar/reactivar módulos.

**Ejemplo conceptual — no es una gramática aprobada:**

```yaml
# Especialización mantenida por el desarrollador
entity: empleados
fields:
  customer_code:
    dictionary: customer.code
  puntuacion:
    minimum: 0
    maximum: 10
    label: Puntuación
```

Aunque la columna física `puntuacion` sea `TINYINT SIGNED` (−128…127), su ámbito funcional es **0…10**. Una columna física `customer_code VARCHAR(10)` puede asociarse al elemento `customer.code` si sus restricciones son compatibles.

### 4.1. Autoría YAML, JSON y APIs nativas

- **YAML** es la forma de autoría preferida por su independencia de Java, C# y PHP y su reutilización al cambiar de stack.
- **JSON** es una representación equivalente del mismo modelo declarativo y resulta útil para pruebas e intercambio.
- Todas las entradas deben resolverse a una **representación semántica neutral** y contractual; las distintas implementaciones deben producir resultados equivalentes.
- **No se exige** crear clases o anotaciones propias en cada lenguaje ni convertir declaraciones en código a archivos YAML.
- Las APIs nativas tipadas podrán añadirse después como mecanismo **opcional** para construir definiciones en memoria que produzcan la misma representación normalizada, no como segunda fuente de verdad obligatoria.
- No se desarrollará un compilador de lenguaje CDS propio para este primer tramo.

## 5. Proyecciones sobre el modelo lógico

### 5.1. Modelo sencillo, sin proyección principal obligatoria

- **El modelo lógico ya es la definición base**; no se introduce una «proyección principal» distinta y obligatoria.
- Una proyección se define sobre el **modelo lógico o sobre otra proyección**.
- Las proyecciones seleccionan explícitamente sus campos y pueden ordenarlos; pueden reducir las operaciones disponibles y referenciar las relaciones permitidas.
- Una proyección derivada **no puede recuperar** campos excluidos por la proyección origen ni ampliar sus capacidades o permisos efectivos.
- Las proyecciones **no pueden cambiar tipos ni límites** ni suavizar restricciones semánticas de su origen. Sí pueden personalizar **etiquetas, descripciones, hints y otros metadatos de presentación** que no alteren el significado ni la validez de los datos.
- **El modelo lógico no se publica automáticamente** como servicio por el mero hecho de existir.
- **Toda proyección pública debe enumerar expresamente sus campos**, sin incorporar automáticamente los campos nuevos del modelo lógico. Así, una nueva columna física nunca aparece accidentalmente en una API.
- Excluir un campo también exige que el backend impida recuperarlo por otros parámetros de consulta, filtros o relaciones no autorizados.

```text
Tabla física: empleados
       │
       ▼
Modelo lógico efectivo: empleados  ── añade automáticamente campos físicos nuevos
       │
       ├── Proyección explícita: empleados.rrhh
       │
       └── Proyección explícita: empleados.logistica
                          │
                          └── Proyección: empleados.logistica.resumen
```

No se equipara una proyección ARP a una `VIEW` SQL, aunque un adaptador pueda servirse de vistas o consultas SQL para resolverla.

### 5.2. Selección de datos y autorización

La proyección es la **frontera explícita de exposición de campos y operaciones**, aplicada **en el servidor**. No sustituye la autorización cuando la aplicación dispone de usuarios, roles o políticas. La ausencia de sistema de autenticación solo se admite cuando el software sea efectivamente público; no permite ampliar campos publicados ni omitir validaciones.

## 6. Servicios, CRUD y comportamiento (D02 y D03)

Cada proyección pública podrá **declarar** qué operaciones ofrece entre `LIST`, `GET`, `CREATE`, `UPDATE` y `DELETE`. Declararlas no significa ejecutarlas ni autorizarlas automáticamente: el servidor aplica límites, validaciones y políticas efectivas.

**Dos modalidades previstas:**

1. **Automática/gestionada:** ARP ejecuta operaciones estándar cuando la proyección y los adaptadores permiten hacerlo sin ambigüedad ni saltarse controles.
2. **Delegada:** ARP invoca operaciones y servicios de la aplicación para cualquier caso con comportamiento propio, transacciones especiales o escrituras no automatizables.

**Alcance inicial aprobado:** automatizar operaciones simples sobre **una sola tabla persistente**, con **clave identificadora**, proyección explícita, operaciones habilitadas, validaciones y controles del servidor. La existencia de una clave no autoriza por sí sola una escritura. Las vistas de lectura, relaciones y consultas más complejas pueden ampliarse posteriormente; las modificaciones entre múltiples tablas se delegan mientras no exista un contrato gestionado que las soporte sin riesgos.

La capacidad de CDS **no se restringe conceptualmente** a una sola tabla; lo limitado es el primer alcance de **CRUD automático**, para demostrar el recorrido y evolucionarlo después.

## 7. Angular y metadatos de presentación (D05)

Una proyección pública aporta información suficiente para que un **cliente Angular genérico** pueda generar:

- **Listado:** columnas seleccionadas, etiquetas, tipos y paginación.
- **Formulario:** campos, controles adecuados, restricciones y literales/hints.
- **Acciones:** alta, consulta, edición y baja, según las operaciones efectivamente disponibles.

No se exige un YAML de pantalla separado para conseguir una UI elemental. Las personalizaciones de presentación son **declarativas y opcionales**, sin modificar tipos, rangos o restricciones del modelo lógico. Se reutilizarán los componentes apropiados de `angular-ui-runtime`; el cliente no conocerá la tabla física ni si el backend es PHP, Java o .NET.

Los controles de cliente ayudan a la usabilidad, pero no sustituyen las comprobaciones del servidor.

## 8. Seguridad, validaciones y errores (D06, D07 y D08)

### 8.1. Seguridad opcional

ARP no impone gestión propia de usuarios, roles o permisos. Si la aplicación dispone de autenticación/autorización, ARP utiliza sus decisiones a través de un mecanismo de integración adecuado. Si es una aplicación pública sin restricciones de identidad, no se requiere ese mecanismo. En todos los casos se respetan las proyecciones, las operaciones declaradas y las validaciones del servidor. Una proyección derivada no puede ampliar los permisos de su origen.

### 8.2. Validación básica y extensibilidad

- ARP valida automáticamente tipos, restricciones intrínsecas del diccionario y restricciones contextuales del modelo lógico.
- Debe poder invocar **validadores propios de la aplicación**, sin incorporar sus reglas empresariales en ARP.
- El **motor de reglas declarativas avanzado**, la orquestación compleja y las integraciones particulares son ampliaciones posteriores; no se precisan para demostrar el primer tramo.
- Las verificaciones de esquema físico nunca deben declarar «compatible» una propiedad que no se haya podido comprobar. Debe distinguirse **compatible**, **incompatible** y **no verificado**.

### 8.3. Diagnósticos contractuales equivalentes

El backend ofrecerá errores normalizados, con códigos y localización de la causa, independientes de las excepciones particulares de cada lenguaje. Las cinco familias funcionales mínimas son:

1. **Definición inválida**: sintaxis, referencia al diccionario o restricciones incoherentes.
2. **Esquema físico incompatible**: discrepancia demostrada entre el esquema real y el modelo lógico.
3. **Dato inválido**: incumplimiento de una restricción al recibir datos.
4. **Operación no permitida**: no declarada, no expuesta o no autorizada, según el contexto.
5. **Fallo de ejecución**: error del adaptador o del servicio de la aplicación.

Cada familia deberá disponer de códigos estables y metadatos suficientes para que Angular presente el error sin interpretar trazas internas. **Los nombres finales, el transporte y el esquema de respuesta son trabajos de `arp-contract`**, no sintaxis fijada aquí.

## 9. Demos, motores y conformidad (D09 y D10)

### 9.1. Distribución

```text
arp-contract/
  examples/demo/          # Definiciones YAML comunes y escenario lógico
  fixtures/               # Casos de conformidad compartidos

arp-java/
  demo/                   # Aplicación autónoma Java + PostgreSQL

arp-dotnet/
  demo/                   # Aplicación autónoma .NET + PostgreSQL

arp-php/
  demo/                   # Aplicación autónoma PHP + MariaDB

cliente Angular común/    # Una sola demo UI; conectable a cualquiera de los tres
```

La disposición es **orientativa**, no impone todavía nombres de paquetes o carpetas. Las tres demos serán independientes de aplicaciones consumidoras, aunque más adelante se validen integraciones con aplicaciones reales. Los archivos lógicos y de proyecciones son compartidos en `arp-contract`; **los archivos físicos difieren** según el motor del ejemplo y se generan desde cada base de datos, no se copian como fuente de verdad común.

### 9.2. Prueba integral mínima

1. Crear una tabla de demo en la base real correspondiente y generar su definición física bajo demanda.
2. Vincular un campo con un elemento del diccionario y restringir otro campo a un subconjunto del rango físico (por ejemplo, `TINYINT SIGNED` frente a `0..10`).
3. Incorporar una columna física nueva y comprobar que aparece en el modelo lógico efectivo **sin** modificar YAML del usuario y **sin** aparecer por defecto en proyecciones públicas.
4. Invalidar la definición física tras una migración; regenerar al siguiente uso. Provocar una incompatibilidad deliberada y verificar que se diagnostica sin borrar las especializaciones lógicas.
5. Desactivar y reactivar un módulo de prueba; sus definiciones de usuario se conservan y sus servicios no se exponen mientras esté inactivo.
6. Crear dos proyecciones públicas diferentes del mismo modelo lógico y, si procede, una derivada; comprobar selección explícita de campos, herencia de límites e imposibilidad de ampliar campos excluidos.
7. Ejecutar y probar las operaciones CRUD simples declaradas, sus validaciones y la vía de ejecución delegada para un caso representativo.
8. Obtener metadatos de presentación y construir **el mismo listado y formulario Angular** contra cada backend, sin código específico para el lenguaje.
9. Comprobar los cinco grupos de errores, y que campos u operaciones no expuestos no son accesibles mediante peticiones directas.
10. Ejecutar en cada runtime las **mismas pruebas compartidas** y mantener evidencia reproducible; los tests locales y la demo no sustituyen la conformidad contractual.

Las pruebas se consideran **criterios de aceptación futuros**, no características ya implementadas.

## 10. Orden acordado de implementación (D11)

1. **`arp-contract` primero:** aprobar formatos y semántica de modelos físicos, lógica, proyecciones, operaciones, metadatos de presentación, diagnósticos y pruebas de conformidad. Reutilizar `ARP-DICT-001` en lugar de redefinirlo.
2. **Runtimes independientes** PHP, Java y .NET: implementar únicamente los contratos aprobados, con pruebas comunes equivalentes. Se permite avanzar progresivamente por stack sin declarar conformidad completa prematuramente.
3. **Demos backend:** demostrar el recorrido real contra PostgreSQL (Java/.NET) y MariaDB (PHP).
4. **Cliente Angular único:** integrar con esos servicios y comprobar listados, formularios y acciones.
5. **Revisión y pulido del bloque:** corregir defectos, documentar resultados y continuar con el siguiente bloque del objetivo global.

No se publicarán versiones parciales por el mero hecho de completar un módulo. **La versión 0.1 no se fijará hasta tener definidos al nivel básico todos los puntos del documento de reorientación.** Después se avanzará en la evolución y maduración del producto hasta conseguir un MVP viable. Esta decisión de planificación no modifica por sí sola las reglas de compatibilidad de eventuales contratos ya publicados.

## 11. Precisiones técnicas todavía por especificar (no reabren los acuerdos)

Estas cuestiones deben resolverse en `arp-contract` al redactar esquemas y casos de prueba; no constituyen permisos implícitos para cambiar el alcance aprobado:

- Identificadores, nombres y gramática definitiva de los YAML físicos, lógicos y de proyección; representación neutral y resolución de referencias.
- Correspondencia de tipos y límites físicos por motor, `VARCHAR` en bytes/caracteres, decimales, fechas, nulabilidad y metadatos no verificables.
- Semántica de compatibilidad con elementos del diccionario, precedencia de restricciones, reglas de ausencia/null y defaults contextuales; respetar el contrato ya aprobado de `ARP-DICT-001`.
- Identidad, actualización parcial, persistencia, transacciones y concurrencia del CRUD gestionado; qué operaciones sobre vistas u objetos sin clave no se automatizan.
- Consulta y navegación de relaciones, filtros/ordenaciones, autorización de campos, operaciones y proyecciones derivadas.
- Notificación/invalidación de cachés en procesos concurrentes o múltiples instancias; atomicidad de generación y fallo recuperable.
- Registro de módulos y resolución de dependencias, proveedores de definiciones/almacenamiento/operaciones/autorización/validación.
- Transporte y esquema concretos de metadatos, resultados y errores consumidos por Angular.
- Determinación de la estructura final de los ejemplos y del repositorio del cliente Angular común.

## 12. Criterios de control

- **No ERP dentro de ARP.** Los nombres empresariales de ejemplos son datos del consumidor, no elementos intrínsecos de la plataforma.
- **No confundir físico con lógico.** El esquema real domina las propiedades físicas; el consumidor domina las especializaciones lógicas y proyecciones.
- **No perder YAML de usuario** por migraciones, regeneraciones o desactivación de módulos.
- **No exponer automáticamente columnas nuevas** en las proyecciones públicas.
- **No confundir capacidad con autorización**, ni controles Angular con seguridad del servidor.
- **No confundir este primer recorrido con el producto completo.** El objetivo mayor sigue siendo diccionario, CDS, comportamientos, reglas, servicios, presentación, extensibilidad y futuras integraciones.
- **No dar por implementado lo que solo está acordado.** La ejecución contractual y las pruebas demostrarán qué funciona en cada stack.

---

**Situación de cierre:** D01–D11 **aprobados en alcance funcional**. Siguiente paso: especificación contractual de este recorrido en `arp-contract`, siguiendo el orden acordado. **No se han modificado repositorios ni publicado versiones mediante este documento.**