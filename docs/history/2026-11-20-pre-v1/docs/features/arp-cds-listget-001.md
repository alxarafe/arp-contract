# ARP-CDS-LISTGET-001 — Lectura mínima de registros

**Estado:** candidato para revisión, no integrado, normativo ni publicado. **Fecha:** 2026-11-17.
Base: [SERVICES-001](arp-services-001.md), [SERVICES-002](arp-services-002.md),
[D01–D11](../decisions/ARP_CDS_modelo_semantico_primera_integracion_Angular.md),
[CDS-READ-001](arp-cds-read-001.md), [MODULES-001](arp-modules-001.md),
[MENUS-001](arp-menus-001.md) y [datos históricos](arp-cds-001-compatibility-and-historical-data.md).

## 1. Corte propuesto

LIST y GET gestionados sobre **una tabla existente con PK demostrada**, modelo lógico efectivo vigente y una
proyección pública explícita registrada por el anfitrión. La resolución CDS existente precede a la lectura;
declarar LIST/GET no aporta autorización ni un ejecutor. No se modifica ninguna gramática de autoría existente.
El registro confiable enlaza destino → proyección → modelo → proveedor; no se deduce del nombre de una tabla.
Las proyecciones derivadas mantienen los subconjuntos de campos y operaciones de CDS-READ-001.

Este primer perfil exige una PK no nula, simple o compuesta, cuyos componentes sean tipos enteros DICT-001
verificados en el modelo efectivo. Su orden es el de la PK física. Limitar las claves a enteros permite demostrar
orden portable sin inventar reglas de colación de texto, zonas horarias o comparación binaria. Otras claves,
vistas, claves alternativas y relaciones quedan sin capacidad gestionada en este corte, no inválidas en CDS.
Cada adaptador debe demostrar identificación única, decodificación exacta, restricciones del servidor y orden.
`not-verified` en compatibilidad de dominios de metadatos no demuestra esa capacidad ni una incompatibilidad:
una lectura puede ofrecerse si su decodificación y capacidades concretas están demostradas. No autoriza escrituras.

Se reutiliza `invocar(request, contexto confiable)` de SERVICES-002, sin imponer una firma o transporte:

```json
{"target":"demo.products","operation":"GET","inputs":{"key":{"reference":"referencia-opaca"}}}
```

Solo `target`, `operation`, `inputs`; entradas GET: solo `key`; LIST: `limit` y/o `continuation`, ambos opcionales.
Un `inputs` ausente/nulo es inválido. LIST `{}` solicita la primera página con límite por defecto del servidor.
No se aceptan nombres físicos, contexto, campos solicitados, filtros, offset, SQL ni orden arbitrario del cliente.
Se adoptan para las entradas decodificadas los presupuestos/perfil portable de CDS-READ-001: 1 MiB, Unicode válido,
claves únicas, profundidad y números exactos. Esto no añade una gramática YAML de servicios ni un protocolo HTTP.

## 2. Identidad sin exposición accidental

La PK completa identifica dentro del destino y ámbito confiable; conocerla nunca concede acceso. Si **todos** sus
campos están publicados y autorizados, la clave neutral es `components`, en orden PK, con nombre, tipo efectivo
y valor en el codec DICT-001. Ejemplo compuesto:

```json
{"components":[{"field":"tenant_id","type":"INT32","value":"7"},
               {"field":"product_id","type":"INT64","value":"9007199254740993"}]}
```

Una clave simple contiene un componente. Se comprueban exactamente componentes, orden, tipos y límites de tipo;
no se acepta una parte implícita de la PK desde el cliente ni un número JSON redondeado. Se reutilizan la gramática
y normalización enteras DICT-001 (`-0` firmado equivale a `0`). No se aplican restricciones de edición actuales
para impedir identificar un registro histórico todavía representable. No hay búsqueda por SKU o clave alternativa.

Si cualquier componente es oculto, `key` contiene **solo** `reference`, opaca, emitida por el anfitrión. No se
exponen nombres, valores parciales, hashes predecibles ni Base64 de la PK. LIST entrega una referencia utilizable
en GET, sin añadir las claves a `values`. El anfitrión demuestra que la referencia no puede falsificarse/derivarse,
vincula propósito GET, destino, proyección, identidad completa, ámbito/identidad cuando exista, revisión de política
y generación; reautoriza cada uso. Puede usar registros privados o evidencia protegida equivalente, no un token
obligatorio de ARP. No es un permiso transferible. Caducidad/revocación requieren invalidar su evidencia.
Los fixtures inyectan referencias predeterminadas: **no** son un generador seguro de tokens.

En modo opaco se rechaza una PK cruda, aunque el solicitante conozca sus columnas. En modo público se exige la PK
tipada. Referencia desconocida, expirada por retirada, fuera de su vinculación o fila inaccesible no revela existencia:
produce la misma salida GET de ausencia. Una referencia vinculada pero de generación anterior se rechaza como
obsoleta; no se usa para confirmar que una fila siga existiendo.

## 3. Resultados y valores

Se conserva SERVICES-002: `status`, `diagnostics` y, solo en éxito, `output`. **No se añade otro estado.**
Las lecturas no emiten `conflict` de actualización. Tampoco usan el `{valid,issues}` de resolución de metadatos.

| Operación | `output` candidato |
| --- | --- |
| GET ausente o fila inaccesible | `{"found":false}` |
| GET encontrado | `{"found":true,"record":{"key":{},"values":{}}}` |
| LIST | `{"records":[],"page":{"limit":2,"hasMore":false,"next":null}}` |

Cada registro incluye `key` según §2 y `values` con **exactamente** los campos de su proyección. El orden de
presentación procede de los metadatos; el orden de miembros JSON de `values` no es semántico. Nunca incluye
campos físicos auxiliares, costes internos, contexto confiable, diagnósticos privados ni valores de otra fila.
La autorización de campo debe permitir toda la proyección registrada; si no, se rechaza la invocación entera.
El host puede registrar una proyección más estrecha, pero el cliente no puede ampliarla ni construirla por parámetros.

Se conserva el valor mediante el codec neutral DICT-001: enteros/decimales exactos como cadenas canónicas,
booleanos reales, textos Unicode sin trim/NFC, fechas y demás escalares según su contrato. No se duplica su
validador. La decodificación del adaptador no puede usar float como paso intermedio ni truncar, redondear o envolver.
Un nulo almacenado se devuelve como `null` solo cuando la nulabilidad física está demostrada; no equivale a un campo
ausente, cadena vacía ni default. Una columna seleccionada ausente, nulo imposible o valor no decodificable falla
la respuesta completa, sin página parcial. Los campos ocultos no se validan para fabricar diagnósticos públicos.

Leer **no revalida como escritura** las restricciones intrínsecas/contextuales actuales. Un `rating=11` histórico,
tipado correctamente, se conserva aunque el modelo actual limite `0..10`; no se recorta, oculta ni normaliza a 10.
El éxito acredita lectura, no validez para editar/regrabar. No se añade un estado histórico ni se exige una UI.
Las restricciones de acceso a la fila se mantienen; “histórico” nunca permite eludir autorización.

## 4. LIST limitado y determinista

El host registra `1 <= defaultLimit <= maxLimit <= 100`. El cliente puede enviar un entero matemático JSON
`1..100` (nunca booleano); se aplica `min(solicitado,maxLimit)`. `page.limit` informa del límite efectivo, no del
número de resultados. Un valor fuera del perfil se rechaza; no existe lectura ilimitada ni total global de filas.

Orden fijo: PK completa ascendente, comparación numérica exacta y lexicográfica entre componentes. La PK única
resuelve todos los empates, incluso si ningún componente se publica. Se restringen filas **antes** de limitar,
calcular `hasMore` o emitir referencias; una página no cuenta ni omite filas debido a registros no autorizados.
El proveedor debe acotar memoria y resultados: como máximo límite + una fila autorizada de anticipación para
calcular `hasMore`. No se promete un plan de acceso físico ni coste constante de BD. El oráculo usa una colección
finita en memoria y no acredita ese límite del proveedor real.

`next` es nulo si no hay más filas autorizadas; en otro caso es una continuación opaca del host. Se vincula al
propósito LIST, destino, proyección, contexto/revisión de política, generación, límite efectivo y última PK completa.
La página siguiente usa estrictamente `PK > últimaPK`; no interpreta un offset ni permite editar los componentes.
La continuación solo posiciona: en cada página se vuelven a autorizar filas y campos. Reutilización fuera de su
vinculación, token desconocido o cambio del límite efectivo se rechazan, sin divulgar el contenido privado.

Con datos y contexto estables, recorrer las páginas devuelve exactamente la secuencia autorizada sin duplicados
ni omisiones, independientemente de cómo enumere filas el proveedor. No se promete una instantánea de datos entre
peticiones: inserciones anteriores al cursor pueden no aparecer; posteriores pueden aparecer; borrados desaparecen.
Cambios de PK pueden mover registros. Una garantía mayor exige otro contrato; no se impone una transacción duradera.

## 5. Seguridad y generaciones

El anfitrión aporta registro activo/módulos, decisiones de filas/campos/operaciones, contexto, proveedor y generación;
`operations` es solo una condición necesaria. No se crea gestión ARP de usuarios, roles o expresiones de políticas.
Una aplicación realmente pública puede carecer de principal, conservando registro, exposición y restricciones.
Destino desconocido/inactivo, operación no expuesta/no autorizada y lectura de campos insuficiente comparten
`rejected`/`operation-not-allowed`/`CDS_LISTGET_UNAVAILABLE`, sin acceso de filas ni diagnóstico de definiciones
ocultas.
Dentro de una operación autorizada, GET ausente y GET de fila inaccesible comparten `found:false`; no se garantiza
igualdad temporal. Las decisiones privadas del arnés **no** son un formato público de permisos.

La generación debe estar vigente antes de leer y al publicar, incluidas páginas vacías y GET ausentes. Se vuelve
a comprobar la autorización y la vinculación del contexto al publicar; si cambian, no sale una respuesta parcial.
Invalidar el físico invalida efectivo, proyecciones, referencias y continuaciones dependientes. Una referencia
obsoleta se rechaza; una invalidación durante el trabajo produce fallo sin `output`. El siguiente acceso reconstruye
según CDS-READ-001; una incompatibilidad no usa el esquema anterior como fallback ni reescribe YAML lógicos.
Una columna nueva puede aparecer en el efectivo, nunca en una proyección que no la enumere. Se requiere coordinación
real del adaptador con la invalidación; una comparación local aislada no prueba ausencia de carreras con DDL externo.
No se promete vigilancia DDL ni coherencia distribuida automática.

## 6. Diagnósticos candidatos

Solo un diagnóstico seguro por rechazo/fallo; sin trazas, SQL, conexión, PK oculta o valores de otras filas.
Autorización suficiente precede a errores de definición/compatibilidad. Después: resolución, exposición/capacidad,
generación, entradas y vinculación, lectura/decodificación, comprobación final antes de publicar.

| Sufijo de `CDS_LISTGET_` | Familia | `status` |
| --- | --- | --- |
| UNAVAILABLE, CAPABILITY_UNAVAILABLE, GENERATION_EXPIRED | operation-not-allowed | rejected |
| INPUT_SHAPE, INVALID_KEY, INVALID_CURSOR | invalid-data | rejected |
| INVALID_DEFINITION | definition-invalid | rejected |
| INCOMPATIBLE_STORAGE | physical-incompatible | rejected |
| READ_FAILED, ROW_DECODE_FAILED, ROW_IDENTITY_INVALID, GENERATION_CHANGED | execution-failure | failed |

Las familias son exactamente las cinco de CDS/SERVICES-002. La ausencia no es error. Un dato almacenado ilegible
no se atribuye al cliente como `invalid-data`; una restricción histórica incumplida tampoco lo convierte en fallo.
`failed` conserva el significado de SERVICES-002, sin prometer rollback ni reintento seguro universal. Este perfil
no hace escrituras de negocio; observabilidad técnica/referencias del host no son una operación de dominio nueva.

## 7. Catálogo modular activo y menús

Se reutilizan el registro, propiedad, dependencias y publicación de MODULES-001. El destino confiable enlaza
una proyección **de la publicación activa**, no una definición encontrada en disco ni una instantánea retirada.
No se descubre ni activa un módulo a partir de `target`. Una proyección aportada por la aplicación funciona
con las mismas condiciones; no se exige que todo consumidor independiente de CDS instale módulos.

El ejemplo reutiliza las fuentes de catalog/reports del escenario MODULES/MENUS, sustituyendo únicamente sus
payloads de artículos por los productos existentes de este borrador. No duplica registros, datos ni validadores:

| Propietario | Aportación sobre products | Operaciones del ejemplo |
| --- | --- | --- |
| Aplicación | Observación física de la tabla | Ninguna exposición pública implícita |
| catalog | Diccionario, commerce.products, products.catalog | LIST permitido; GET se autoriza por separado |
| reports | products.summary, derivada de products.catalog: sku y name | Solo LIST; depende directamente de catalog |

“Derivada” sigue significando subconjunto CDS de campos/operaciones sobre la misma entidad: no añade agregados,
joins ni SQL. La proyección identificada de los vectores originales sigue comprobando claves públicas; no se
expone automáticamente por activar catalog. La aplicación registra cada destino/proyección explícitamente.

Desactivar reports retira su consulta pública y conserva catalog; retirar catalog requiere retirar también reports.
Consultar una proyección retirada devuelve UNAVAILABLE sin tocar el proveedor. Una dependencia no declarada impide
aceptar la composición. La desactivación no borra archivos ni filas. Cambiar la composición durante una lectura
invalida su evidencia antes de publicar; no sirve continuar usando el viejo catálogo porque la tabla aún exista.

Las decisiones por operación del host se usan también en los fixtures de MENUS: LIST permitido no concede GET.
Una opción visible, oculta o excluida del menú nunca es un permiso ni revoca por sí sola una operación del servidor.
Invocar directamente repite catálogo activo, exposición, operación, campos y restricciones de filas. El cliente
no puede suministrar `active`, `projectionAccess` ni contexto dentro de inputs para cambiar esas decisiones.

Los descriptores de consulta y sus dependencias viven en la **única caché general de la aplicación**. Se reutiliza
el plan MODULES-001: retirar reports invalida su descriptor y mantiene el de catalog y el físico no afectado;
retirar ambos invalida los dos descriptores. No se introduce caché de resultados de filas, almacenamiento por módulo,
ARP-CACHE-001 ni un segundo protocolo de generaciones. Referencias y continuaciones siguen §2/§4/§5.
El oráculo puede invalidar conservadoramente una lectura en vuelo al cambiar una fuente activa, incluso de menú;
no exige reconstruir en producción derivados cuyas dependencias completas se demuestren ajenas al cambio.

## 8. Frontera mínima con persistencia real

Esta sección describe responsabilidades y datos semánticos, **no** otra gramática pública, interfaz obligatoria
ni serialización de un plan de consulta. El anfitrión valida SERVICES-002, resuelve CDS/MODULES y autoriza antes
de llamar al adaptador. Puede materializar estos datos en objetos, funciones o servicios propios de cada runtime.

| El adaptador recibe del anfitrión confiable | Condición |
| --- | --- |
| Proveedor, tabla y generación | Registro y físico vigentes; nunca nombres libres del cliente |
| Modelo efectivo, columnas, tipos y nulabilidad | Lectura y decodificación exactas demostradas |
| LIST/GET y campos exactos | Columnas públicas seleccionadas y PK interna para ordenar/identificar |
| Restricción de filas y contexto confiable | Antes del límite/anticipación; nunca un filtro del solicitante |
| GET: PK completa tipada y normalizada | Referencia opaca ya verificada/resuelta por el host |
| LIST: límite, PK ascendente y última PK opcional | Límite + una autorizada; sin offset/orden/campos libres |
| Evidencia de vigencia | Proyección, dependencias y revisión de acceso; coordinación con invalidación real |

Si un adaptador no puede ejecutar la restricción del servidor antes de paginar, no tiene capacidad para esta
consulta: no obtiene una página sin restringir para filtrarla después ni escanea resultados ilimitados en el host.
Puede usar las abstracciones de autorización/persistencia de la aplicación; ARP no define aquí un lenguaje de
predicados ni un sistema de permisos. Los identificadores físicos se resuelven de manera segura; los valores se
parametrizan mediante las capacidades del proveedor. No se interpretan entradas del cliente como SQL.

| El adaptador devuelve al anfitrión | Responsabilidad posterior |
| --- | --- |
| GET: cero o una fila autorizada | Cero combina ausencia/inaccesibilidad; no devuelve motivo privado de denegación |
| LIST: hasta límite + una, autorizadas en orden PK | Retirar anticipación, calcular hasMore y emitir cursor |
| Cada fila: valores y PK interna | Codec DICT exacto, sin float; nulo explícito; PK oculta fuera de values |
| Fallo de lectura/identidad/codec | Diagnóstico seguro de §6; sin excepción/SQL ni respuesta parcial |
| Evidencia de vigencia/invalidación | Reautorizar y comprobar generación; el host controla la publicación |

Una segunda fila para la misma PK indica fallo de identidad, no selección arbitraria de la primera. El adaptador
no emite tokens públicos ni decide ampliar la proyección. El host puede comprobar identidades por página, pero
la unicidad física de la PK debe demostrarse previamente: el oráculo finito no acredita esa garantía de una BD.
Tampoco se exige al proveedor devolver `{status,diagnostics,output}`: esa envoltura sigue perteneciendo a la
invocación SERVICES-002. No se promete una transacción o snapshot entre páginas; se mantienen las reglas de §4.

Las obligaciones nativas amplían el mismo manifiesto, sin nuevos conjuntos de productos. PostgreSQL (.NET/Java)
y MariaDB (PHP) son los entornos de conformidad ya propuestos, no dependencias normativas de esos lenguajes.
El siguiente trabajo implementará una tabla real, codec, aplicación de restricciones y evidencia de generación
por runtime. No queda pendiente otra decisión funcional para empezar este perfil: se requiere revisar/aceptar
este contrato y demostrar las obligaciones en cada adaptador. Las PK no enteras quedan fuera de este corte,
sin declarar inválidos sus modelos ni abrir ahora reglas nuevas de colación u otros tipos de identidad.

## 9. Evidencia y revisión

- [Datos y definiciones](../../../../../fixtures/cds/listget/v1/products.json): productos comerciales concretos, autorados
  para prueba, sin datos privados ni extracción de BD. PK simple/compuesta y gramáticas CDS/DICT existentes.
- [88 vectores](../../../../../fixtures/cds/listget/v1/cases.json): expectativas explícitas; no generadas por el oráculo.
  `defaults` + sustitución de miembros superiores de `host` son solo composición del arnés; no una gramática ARP.
  Se preservan los 74 originales y se añaden 14 modulares sobre los mismos datos. `moduleState`,
  `moduleStateAtPublish` y `authorizedOperations` son evidencia privada del host, no entradas de consumidores.
- [Esquema de resultados](../../../../../schemas/cds/v1/listget-result.schema.json): perfil candidato de salida SERVICES-002,
  sin añadir estados ni alterar esquemas anteriores; la selección exacta de campos depende de la proyección.
- [Obligaciones nativas](../../../../../fixtures/cds/listget/v1/provider-obligations.json): PostgreSQL para .NET/Java y
  MariaDB para PHP, aún **sin ejecutar**. Deben partir de tabla real, observarla y verificar los mismos valores,
  políticas, precisión, fallos, invalidación e invariancia de las definiciones lógicas.
- [Oráculo](../../../../../tools/check_cds_listget_draft.py) y [regresiones](../../../../../tests/test_cds_listget_draft.py):
  reutilizan resolver CDS y límites enteros DICT. Las demás celdas representan salida ya decodificada por el
  adaptador; `decodeFailures` simula su fallo. No duplican los 17 validadores ni prueban su decodificación real.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_cds_listget_draft.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
git diff --check
```

Pendiente de revisión: aprobar este perfil y su codec neutral, no un transporte. Después corresponden las pruebas
reales en los tres runtimes, referencias/continuaciones protegidas e intercalados de invalidación/autorización.
No se ejecuta SQL ni se implementan endpoints, Angular, escritura, ORM, filtros arbitrarios, permisos propios,
ARP-CACHE-001 o nuevas gramáticas de autoría. No se integrará ni publicará este candidato sin revisión.

Validación local de la propuesta: **88 vectores LIST/GET, 180 pruebas Python y nueve verificadores** correctos.
Se conservan las 151 pruebas de main y las 22 regresiones del borrador; se añaden siete regresiones modulares.
CI ejecuta también el verificador LIST/GET. Sin ejecuciones nativas, SQL, criptografía ni de BD.
No hay formateador configurado en la raíz: se comprueban UTF-8, LF, sangría, longitud y whitespace de los nuevos
archivos, sin reformatear los anteriores.