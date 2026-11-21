# ARP-SERVICES-002 — Invocación neutral y resultados

**Estado:** especificación funcional candidata, no normativa ni publicada.
**Fecha:** 2026-11-16. **Dependencias:** [arquitectura](../architecture.md),
[D01–D11](../decisions/ARP_CDS_modelo_semantico_primera_integracion_Angular.md),
[CDS](arp-cds-001.md), [datos históricos](arp-cds-001-compatibility-and-historical-data.md) y
[SERVICES-001](arp-services-001.md). No modifica esos acuerdos ni la gramática de proyecciones.

## 1. Objetivo y alcance

Definir el significado observable de una invocación a un destino registrado y sus resultados, común a ejecución
local, adaptadores futuros y consumidores diversos. El corte actual entrega documentación, vectores y un oráculo
estático; no implementa un runtime ni publica un formato, API, endpoint o esquema obligatorio.

La aplicación registra destinos y operaciones explícitamente habilitados, contratos de entrada/salida y manejadores.
La resolución no ejecuta nombres de clases, métodos, rutas, SQL ni expresiones proporcionadas por el solicitante.
La existencia de un destino o de metadatos no concede acceso. Las operaciones gestionadas requieren las capacidades
comprobadas de SERVICES-001; las delegadas siguen siendo responsabilidad de la aplicación.

CRUD y servicios pueden compartir este mecanismo neutral de invocación y resultados sin compartir su origen
declarativo. Compartir el despacho no unifica sus garantías ni sus contratos de entrada/salida.

Queda abierto si los CRUD se generan desde proyecciones, YAML independientes o ambas opciones. `operations` de
`arp.projection/v1` conserva su significado vigente. No se añaden roles obligatorios ni definiciones visuales.

## 2. Entrada y contexto confiable

Notación **candidata**, expresable como valores en memoria sin HTTP:

```json
{
  "target": "demo.items",
  "operation": "UPDATE",
  "inputs": {
    "key": "item-1",
    "changes": {"price": "60"},
    "baseline": {"price": "50"}
  }
}
```

- `target`: identidad lógica resuelta exclusivamente en el registro activo de la aplicación.
- `operation`: identificador habilitado dentro del destino. Las cinco capacidades CRUD conservan su significado;
  un manejador delegado puede tener otra operación registrada, sin ampliar la gramática de proyecciones.
- `inputs`: entradas según el contrato registrado. `key` identifica el registro dentro del ámbito confiable;
  conocer una clave no demuestra acceso. Consultas, altas y operaciones delegadas tendrán sus propios contratos.
- Para UPDATE, `changes` contiene solo los campos solicitados y `baseline` las precondiciones de cada campo incluido.
  Estos nombres no fijan el mecanismo futuro de precondiciones ni exigen devolver valores base como protocolo final.
- `confirmation`, opcional en estos ejemplos, referencia evidencia de confirmación comprobable por el servidor;
  no es un booleano que autorice una sobrescritura ni un permiso reutilizable universal.

El invocador confiable suministra **por separado** identidad si existe, ámbito, políticas y decisiones de acceso,
registro activo y capacidades. El servidor los obtiene de la aplicación, también en ejecución local. Una aplicación
realmente pública puede no tener identidad ni autenticación; sigue imponiendo exposición, validación y restricciones.
Los datos del cliente nunca acreditan identidad, autorización, tenant ni ámbito. Los selectores de contexto que una
aplicación admita son entradas no confiables y deben resolverse y autorizarse de nuevo.

El perfil de prueba rechaza propiedades desconocidas, incluidos intentos de introducir contexto confiable en la
petición. Es una elección acotada de los vectores, no un sistema de extensiones publicado. La separación conceptual
es `invocar(petición, contexto confiable)`: no obliga a una firma de lenguaje ni a importar tipos ARP en el dominio.

## 3. Presencia, validación y cambios efectivos

Las reglas de actualización de esta sección y las garantías gestionadas de la siguiente corresponden al UPDATE
parcial de SERVICES-001. No se extienden automáticamente a cualquier servicio delegado.

Un campo **ausente** de `changes` no se escribe ni se rellena desde copias antiguas. Un `null` presente solicita
escribir nulo y debe cumplir nulabilidad y restricciones. Una base explícitamente nula es una precondición de nulo;
una base ausente es falta de precondición, no una base nula ni permiso para escribir a ciegas.

`inputs` ausente o nulo no significa mapa vacío en el perfil de prueba. `changes: {}` es una actualización sin
campos; no equivale a reemplazar el registro. La presencia/defaults de CREATE y el modelo general de campos
opcionales siguen pendientes. Los campos de demostración son persistentes y presentes; sus valores numéricos son
cadenas exactas como en SERVICES-001. Los tres campos de estos vectores no admiten nulo.

El servidor valida cada campo incluido, incluso si coincide canónicamente con el persistido. Por tanto reenviar
un `rating=11` histórico sigue siendo inválido aunque no produciría diferencia. Un histórico inválido **omitido**
permanece intacto; no se exige revalidarlo individualmente por leerlo. Las invariantes dependientes sí se comprueban.
Se aplican diccionario, restricciones contextuales, exposición, permisos y validadores de la aplicación.

Tras autorización, validación y precondiciones, solo se persisten campos cuyo valor difiere del actual mediante
comparación tipada/canónica. Un cambio concurrente del mismo campo produce conflicto aunque el propuesto ya coincida
con el actual. No se elimina primero ese campo para esconder el conflicto. Sin diferencias efectivas, el resultado
es éxito con `changed: false`: no hay escritura ni efecto de negocio por guardar, aunque siguen los controles.
Esto no impide observabilidad técnica autorizada. Decimales y equivalencia general requieren reglas del contrato
de tipos; el pequeño oráculo solo compara los ejemplos exactos de SERVICES-001.

## 4. Concurrencia, confirmación y atomicidad

**Operaciones gestionadas:** el proveedor debe demostrar las garantías exigidas para la operación ofrecida.
Para UPDATE parcial se conservan las reglas de SERVICES-001 descritas a continuación.

**Operaciones delegadas:** el contrato registrado de cada operación debe declarar sus garantías y límites;
la aplicación y su manejador son responsables de cumplirlos. El mecanismo común no les atribuye por sí mismo
atomicidad, control de concurrencia ni rollback. Un delegado que ofrezca el UPDATE parcial de SERVICES-001 debe
cumplir sus reglas y demostrar esas garantías; registrarlo no constituye esa evidencia. La exposición, validación
y autorización del servidor se aplican siempre, también al despacho delegado.

Para cada campo incluido se compara el valor actual con la base, o con el actual expresamente confirmado.
Un cambio en otro campo se conserva y no causa por sí solo conflicto, sin eximir de invariantes dependientes.
Si cualquier campo entra en conflicto, falla validación o pierde autorización, no se guarda ningún campo del conjunto.

La comparación final y la escritura completa deben ejecutarse bajo una garantía indivisible comprobable del
adaptador, como protección transaccional o compare-and-swap apropiado. Una lectura seguida de escritura sin
protección no cumple. Las dependencias de reglas y políticas también necesitan protección o reevaluación que evite
usar decisiones obsoletas al persistir. Si el adaptador no puede garantizarlo, no ofrece UPDATE gestionado seguro.
Un fallo de persistencia anterior al commit debe revertir toda la actualización gestionada; nunca devolver
éxito parcial. Una pérdida de certeza sobre el commit no demuestra rollback (véase la sección 5).

La confirmación de conflictos es una **capacidad específica** de las operaciones que la ofrecen, no una entrada
ni una exigencia universal para todos los servicios. Un servicio sin esta capacidad no tiene que aceptar
confirmaciones. En el UPDATE aquí modelado permite solicitar una sobrescritura expresa; nunca sustituye la
autorización ni habilita operaciones que el servidor no permita.

Cuando se ofrece esta capacidad, la confirmación debe estar vinculada a destino, operación, registro, campos,
propuesta y precondiciones relevantes, ámbito e identidad cuando exista. El servidor comprueba evidencia de
confirmación expresa; no basta con aceptar
un `confirmedCurrent` arbitrario como autoridad. Cambiar la propuesta o el contexto exige nueva confirmación.
Expiración, invalidación y pérdida de permisos impiden reutilizarla. En cada intento se revalidan reglas y permisos;
la confirmación nunca los sustituye. Antes de persistir se compara **atómicamente** con el actual confirmado:
si ha cambiado de nuevo, hay otro conflicto y ningún efecto de esa petición.

El fixture usa un identificador opaco y evidencia en memoria suministrada por el anfitrión. No prescribe tokens
firmados, almacenamiento de sesiones, duración, consumo único ni algoritmo criptográfico. La forma final de demostrar
el consentimiento y evitar falsificación/reutilización indebida queda pendiente, manteniendo estas propiedades.

Comparar valores detecta divergencia actual, **no episodios ABA** (A→B→A). El vector correspondiente acepta la
actualización porque la base vuelve a coincidir; no demuestra detección histórica. Una garantía mayor requiere
revisión por campo u otra evidencia demostrable, aún sin elegir. No se impone revisión global que cause conflictos
por cambios independientes.

## 5. Resultados y diagnóstico normalizado

Todos los nombres y códigos siguientes son candidatos. Los resultados tienen un discriminador `status` y una lista
`diagnostics`; no requieren excepciones particulares, códigos HTTP ni interpretación de textos humanos.

| `status` | Significado | Contenido candidato |
| --- | --- | --- |
| `success` | Operación completada según su contrato | `output` tipado y autorizado; UPDATE informa `changed` |
| `conflict` | Divergencia concurrente, sin escritura | `conflictCode: CONCURRENT_CHANGE` y detalles autorizados |
| `rejected` | Petición no ejecutable por controles o decisión de negocio | Diagnósticos seguros; sin salida exitosa |
| `failed` | No se pudo completar por fallo de ejecución | Diagnóstico seguro; nunca implica éxito ni reintento seguro |

Se conservan exactamente las cinco familias CDS para diagnósticos:

| Familia candidata | Ejemplos de causa |
| --- | --- |
| `definition-invalid` | Referencia o contrato registrado incoherente |
| `physical-incompatible` | Incompatibilidad física demostrada |
| `invalid-data` | Forma/valor inválido, precondición ausente, rechazo de regla de negocio |
| `operation-not-allowed` | Operación no expuesta, no autorizada o capacidad no disponible |
| `execution-failure` | Fallo del manejador o adaptador |

Un diagnóstico lleva `family` y `code`; podrá incluir localización lógica y argumentos aprobados cuando no filtren
información. Mensajes/localización e inventario definitivo de códigos quedan pendientes. Una entrada mal formada
no se confunde con una definición registrada inválida. `not-verified` no se etiqueta incompatibilidad demostrada:
los vectores rechazan la capacidad gestionada como no disponible. Un rechazo empresarial no es automáticamente
un fallo técnico. El conflicto es un resultado funcional explícito, **no una sexta familia CDS** ni un fallo de
ejecución genérico. En los vectores tiene `diagnostics: []` y detalles propios.

El resultado local y el adaptado deben preservar el mismo significado. **`failed` no acredita ausencia de efectos**:
un manejador delegado puede haber producido efectos antes de fallar, incluso durante una llamada local. También
puede perderse la certeza sobre el commit o su respuesta. Se distinguen conceptualmente:

- **Rollback conocido:** existe evidencia de reversión completa dentro del alcance transaccional declarado.
  El vector `commit-rollback` modela ese caso de UPDATE gestionado; no acredita reversión de efectos externos.
- **Resultado desconocido:** no existe evidencia suficiente para asegurar al consumidor si hubo efectos.
  La misma respuesta `failed` puede corresponder a una ejecución sin efectos o con efectos ya producidos.
  No debe interpretarse como garantía de rollback ni de ausencia de persistencia.

Esta distinción no introduce un nuevo estado definitivo ni fija metadatos públicos para comunicar la certeza.
Los vectores delegados de fallo conservan la misma respuesta pública y varían solo la observación privada de
los efectos sintéticos. No se define reintento automático, idempotencia o certeza de entrega; `failed` no autoriza
repetir una mutación. La representación final y el tratamiento de efectos desconocidos y externos siguen abiertos.

## 6. Información autorizada y orden de ejecución

El servidor restringe registro, operación, campos y salida, también errores. Un conflicto solo puede mostrar
`original`, `actual` y `propuesto` de campos cuya lectura esté autorizada. No revela valores ocultos, claves ajenas,
identidades de terceros, trazas, detalles físicos ni secretos. Sin lectura suficiente devuelve un rechazo seguro
sin conflictos ni opción de confirmar información que el usuario no puede ver. La pérdida de lectura invalida
la posibilidad de usar la confirmación anterior aunque permanezca permiso de escritura.

El perfil de prueba usa `UNAVAILABLE` para destino desconocido, operación no habilitada y registro inaccesible, sin
confirmar su existencia. La precedencia técnica final queda abierta: antes de divulgar diagnósticos de definición,
compatibilidad o conflicto se necesita autorización suficiente. No se promete igualdad temporal de las respuestas.
El host debe filtrar también los resultados delegados; registrar un manejador no autoriza publicar todo lo que devuelve.

## 7. Evidencia, aceptación y límites

[Fixtures](../../../../../fixtures/services/v1/invocation-cases.json),
[verificador](../../../../../tools/check_service_invocation_draft.py) y
[tests](../../../../../tests/test_service_invocation_draft.py) separan `request`, `host` y `expected.response` de
`expected.observed`. **`host` y `observed` son instrumentación privada de prueba**, jamás partes de la respuesta.
Esta separación permite verificar persistencia y efectos sin devolver el registro completo al consumidor.

Los vectores cubren despacho local delegado, formas inválidas, las cinco familias, autorización, campos ocultos,
concurrencia independiente y del mismo campo, confirmación vigente/obsoleta, carrera al commit, rechazo atómico,
fallo con rollback conocido, fallo delegado con efectos desconocidos para el consumidor, ausente/null, históricos
y ausencia de cambios efectivos. Se reutiliza el oráculo de UPDATE de SERVICES-001 sin modificar sus casos ni
semántica. Las expectativas están almacenadas explícitamente.
Los tests comprueban además propiedades por grupos y variaciones de entradas, no solo que el JSON se pueda leer.

Ejecución desde la raíz, con las dependencias de desarrollo ya existentes:

```sh
python3 tools/check_service_invocation_draft.py
python3 -m unittest discover -s tests -v
git diff --check
```

El oráculo simula una frontera indivisible mediante `currentAtCommit`; **no demuestra transacciones, bloqueos,
autorización real, protección criptográfica, aislamiento, seguridad temporal ni conformidad Java/.NET/PHP**.
Su delegado `inspect` es sintético: devuelve salida preaprobada o un fallo; en los escenarios de resultado
desconocido se instrumenta si produjo un efecto antes de fallar, sin revelarlo en la respuesta. No requiere
confirmación y no acredita atomicidad, concurrencia ni rollback del delegado. No se ejecutan SQL, HTTP ni Angular.
El objetivo futuro exige pruebas reales de intercalado y fallos en cada adaptador antes de afirmar garantías.

## 8. Decisiones abiertas

- Gramática definitiva, identificadores, extensiones, serialización, contratos tipados de entrada/salida y códigos.
- Origen declarativo de CRUD y enlace de servicios con proyecciones; `operations` permanece intacto.
- Mecanismo verificable de precondiciones/confirmación, caducidad, reutilización y eventual detección de ABA.
- Presencia, defaults, nulabilidad contextual, CREATE, DELETE y consultas/paginación/filtros autorizados.
- Evidencia exigible de atomicidad y protección de reglas dependientes en cada adaptador.
- Reintentos, idempotencia, efectos externos, resultado desconocido, asincronía y transacciones entre entidades.
- Mapeo HTTP, adaptación Angular y otros consumidores, negociación de capacidades y localización de mensajes.

No hay cambios de runtime, versión, etiqueta ni release. El borrador no afirma conformidad nativa ni sustituye
los contratos integrados; requiere revisión contractual antes de implementaciones posteriores.