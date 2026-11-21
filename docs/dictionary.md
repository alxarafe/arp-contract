# ARP-INTEGER-001 — Diccionario y enteros exactos

**Especificación del candidato activo, pendiente de revisión de la PR; sin publicación ni conformidad de runtimes.**
Este cambio incompatible sustituye los siete tipos enteros anteriores en `arp.dictionary/v1`.
La [nota de alcance, pruebas y ajustes de arp-php](features/arp-integer-001.md) forma parte de esta especificación.
El resto de ARP-DICT-001 y de su perfil de portabilidad conserva las reglas archivadas en
[ARP-DICT-001](history/2026-11-20-pre-v1/docs/features/arp-dict-001.md) y
[portabilidad 002](history/2026-11-20-pre-v1/docs/dictionary-portability-002.md).
En caso de discrepancia sobre enteros, prevalece este documento.

## Sintaxis y dominio representable

Los tipos activos son `BOOLEAN`, `STRING`, `TEXT`, `INTEGER`, `DECIMAL`, `UUID`, `DATE`, `TIME`, `DATETIME`,
`ENUM` y `BINARY`. `INT8`, `UINT8`, `INT16`, `UINT16`, `INT32`, `UINT32` e `INT64` se rechazan, sin alias.
Tampoco existe un identificador `UINT64`; la capacidad sin signo de 64 bits se expresa mediante `INTEGER`.

```yaml
apiVersion: arp.dictionary/v1
elements:
  - id: demo.score
    type: INTEGER
    constraints:
      bits: 16
      signed: true
      minimum: '0'
      maximum: '100'
      multipleOf: '2'
```

Todas estas propiedades pertenecen a `constraints`, que es opcional y equivale a `{}` cuando se omite.
`bits` admite únicamente los enteros matemáticos `8`, `16`, `32`, `64`; `signed` es booleano.
No se convierten cadenas a números ni números a booleanos; `null` no equivale a omisión.
Las reglas de intake exacto para metadatos numéricos siguen vigentes: un nodo JSON `8.0` representa el entero
matemático 8; `"8"`, `true` y `8.5` no son un `bits` válido.
`exclusiveMinimum` y `exclusiveMaximum` son booleanos opcionales, por defecto `false`.
`minimum`, `maximum` y `multipleOf` son cadenas decimales enteras exactas.
Las propiedades ajenas al tipo se rechazan.

Para la capacidad resuelta `(N, signed)`, el dominio representable `D = [dmin, dmax]` es:

| Signo | dmin | dmax |
| --- | --- | --- |
| `true` | `-2^(N-1)` | `2^(N-1)-1` |
| `false` | `0` | `2^N-1` |

La capacidad indica representación; no implica que todos sus valores sean lógicamente válidos ni exige un
primitivo de igual tamaño en el lenguaje o en SQL. Los valores extremos de 64 bits son
`-9223372036854775808`, `9223372036854775807` y, sin signo, `18446744073709551615`.

## Inferencia determinista

Se resuelve una sola vez sobre la declaración intrínseca, antes de restricciones contextuales o datos:

1. Validar tipos y léxico; interpretar límites exactamente, normalizando `-0` numéricamente a cero.
2. Si se declara `signed`, respetarlo. Si se omite, usar `false` cuando existe un `minimum >= 0`;
   usar `true` en cualquier otro caso. Un `maximum` positivo por sí solo no permite inferir sin signo.
3. Si existe `bits`, respetarlo sin ampliarlo ni reducirlo. Si se omite y existen ambos límites,
   elegir el primer tamaño de `[8, 16, 32, 64]` que represente **los dos límites declarados** con ese signo.
   Si falta uno o ambos límites, probar únicamente `[32, 64]`. No reducir a 8 o 16 por un único límite.
4. Si ningún candidato sirve, rechazar la definición. Ambos límites declarados deben pertenecer a `D`,
   aun siendo exclusivos. No cambiar el signo para hacerlos caber; no inferir desde valores de datos,
   observaciones SQL, defaults ni `multipleOf`.
5. Rechazar `minimum > maximum`. Calcular el intervalo lógico como se indica debajo y comprobar que
   contiene al menos un valor válido.

| Restricciones declaradas | bits | signed |
| --- | --- | --- |
| `{}` | 32 | `true` |
| `minimum: '0'` | 32 | `false` |
| `maximum: '100'` | 32 | `true` |
| `minimum: '4294967296'` | 64 | `false` |
| `maximum: '-2147483649'` | 64 | `true` |
| `minimum: '0', maximum: '100'` | 8 | `false` |
| `minimum: '-100', maximum: '100'` | 8 | `true` |
| `minimum: '0', maximum: '200', signed: true` | 16 | `true` |
| `minimum: '0', maximum: '100', bits: 16` | 16 | `false` |
| `minimum: '0', maximum: '100', bits: 16, signed: true` | 16 | `true` |
| `minimum: '0', maximum: '18446744073709551615'` | 64 | `false` |

`maximum: '18446744073709551615'` sin mínimo ni signo es inválido: el signo inferido es `true`.
`bits: 8, maximum: '256', exclusiveMaximum: true, signed: false` también es inválido: el límite
**declarado** no cabe. Sin `bits`, `minimum: '0', maximum: '256', exclusiveMaximum: true` deriva 16 bits,
aunque sus valores admitidos sean `0..255`. Esta decisión cierra expresamente la ambigüedad del boceto inicial.

## Restricciones lógicas y contradicciones

Partir de `[L, U] = D`. Un mínimo declarado sustituye `L` por ese mínimo, sumando uno si es exclusivo.
Un máximo declarado sustituye `U` por ese máximo, restando uno si es exclusivo.
Un extremo exclusivo `true` exige su correspondiente límite; `false` sin límite no tiene efecto.
Rechazar `L > U`, incluidos intervalos abiertos que no contienen enteros.

`multipleOf` debe ser un entero estrictamente positivo `m`; cero, negativos, fracciones y nodos numéricos
son inválidos. Un valor `v` lo satisface si existe un entero `k` tal que `v = k*m`, incluidos cero y negativos.
El primer múltiplo en el intervalo es `ceil(L/m)*m`; rechazar la definición si supera `U`.
Esta comprobación usa división matemática hacia menos infinito y aritmética exacta, también para límites negativos.
El múltiplo no necesita caber en `D`: `minimum: '0', maximum: '0', multipleOf: '18446744073709551616'`
es válido porque admite cero. `1..2, multipleOf: '3'` y `-2..-1, multipleOf: '3'` son inválidos.

Una capacidad explícita más amplia no relaja límites: con 16 bits y `maximum: '100'`, `101` sigue siendo inválido.
Ningún dato amplía capacidad ni restricciones. No se recortan límites silenciosamente al rango de almacenamiento.

## Valores, normalización, límites y errores

El transporte neutral de valores, límites y múltiplos usa cadenas con léxico ASCII
`-?(0|[1-9][0-9]*)`, consumiendo la cadena completa. No se admiten signo `+`, espacios, ceros iniciales,
fracciones, exponentes, dígitos Unicode, booleanos ni nodos JSON/YAML numéricos como valores escalares enteros.
`-0` se acepta con cualquier signo y se normaliza a `"0"`; el signo lógico restringe el número, no el léxico.
La normalización devuelve la cadena decimal canónica sin redondeo, saturación ni truncamiento.

La implementación debe preservar exactamente valores adyacentes superiores a `2^53`, todos los límites de
64 bits y comparaciones, ordenación, módulo, igualdad y serialización. No puede pasar por `float`, `double`
ni JavaScript `Number`. La representación interna es libre si demuestra estas propiedades.
El presupuesto de cadenas numéricas sigue siendo de 4096 caracteres; sobrepasarlo produce
`DICTIONARY_LIMIT_EXCEEDED`. Se conservan los demás presupuestos de intake de portabilidad 002.

Una definición inválida produce `DICTIONARY_ELEMENT_INVALID` antes de publicar su catálogo.
Para una definición válida, léxico o tipo de nodo incorrecto produce `DICTIONARY_VALUE_TYPE`.
Los incumplimientos numéricos se acumulan como `DICTIONARY_VALUE_CONSTRAINT`, en este orden:
`typeRange`, `minimum`, `maximum`, `multipleOf`. `typeRange` compara con `D`; los otros comparan con las
restricciones declaradas, incluidas exclusiones. Nunca se devuelve `normalizedValue` si hay errores.
Los límites de recursos tienen prioridad sobre la evaluación aritmética.

## Descriptores, CDS e identidad

El descriptor del diccionario conserva restricciones y metadatos declarados y materializa `bits` y `signed`
resueltos. CDS conserva además las restricciones intrínsecas y contextuales por separado; su descriptor efectivo
materializa capacidad y límites inclusivos efectivos. Aplicar un contexto más restrictivo no vuelve a inferir
capacidad ni signo. Un contexto no puede ampliarlos ni debilitar las restricciones intrínsecas.
El oráculo CDS mantiene su perfil acotado: restricciones contextuales de intervalo, sin convertirlo en un
resolutor general de `multipleOf` ni afirmar compatibilidad cuando no la ha demostrado.

El escalar físico normalizado es `INTEGER`; `nativeType` sigue siendo texto opaco del adaptador.
La evidencia física se expresa en `integerRange`, con límites exactos observados, sin inferir 32 bits por el nombre.
Un lado conocido puede probar incompatibilidad; para probar contención hacen falta ambos lados.
Ausencia o evidencia parcial da `not-verified` si no hay conflicto demostrado. Los límites de un `INTEGER`
físico normalizado deben estar en la unión de las capacidades de hasta 64 bits.
Un campo sin diccionario solo puede derivar capacidad de una observación completa; una observación parcial
no inventa tipo lógico ni capacidad. Esto no activa creación de tablas ni nuevos estados de compatibilidad.

Las claves simples y compuestas usan componentes `{field, type: "INTEGER", value: "..."}` en el orden de la PK.
La capacidad se obtiene del descriptor confiable del campo, nunca de propiedades adicionales aportadas por la
petición. No se añaden `bits` ni `signed` a cada componente. Se rechazan tipos antiguos y capacidades desbordadas.
Normalizar antes de comparar identidades y detectar duplicados; ordenar numéricamente, sin ordenar cadenas.
No reaplicar límites de negocio actuales a una identidad histórica representable.
Referencias opacas y cursores conservan sus enlaces a destino, proyección, contexto y generación.

CREATE valida capacidad, restricciones lógicas y físicas de todos los valores efectivos, incluidos defaults.
UPDATE valida cada valor enviado aunque no cambie, conserva ausentes y compara baseline exactamente;
se mantienen conflictos, confirmación, atomicidad y resultados inciertos. DELETE valida la identidad exacta y
su evidencia de lectura; no revalida como datos nuevos los valores históricos fuera de restricciones de negocio.
LIST/GET preserva identidades exactas, claves ocultas y ordenación. Ningún cambio de tipo concede permisos,
capacidad de ejecución o validez de precondiciones; siguen vigentes todas las barreras de publicación y escritura.