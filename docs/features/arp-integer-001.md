# ARP-INTEGER-001 — Unificación de tipos enteros

**Estado:** especificación definitiva de esta propuesta para revisión de PR; candidato activo sin publicar.
**Base:** `c1831e2`, coincidente con `origin/main` al iniciar este trabajo.
**Semántica y precedencia:** [Diccionario e INTEGER](../dictionary.md).
No se fusiona automáticamente ni se afirma conformidad de PHP, Java o .NET.

## Ruptura y alcance

Se sustituyen `INT8`, `UINT8`, `INT16`, `UINT16`, `INT32`, `UINT32` e `INT64` por `INTEGER` en los artefactos
activos del repositorio. `bits` y `signed` son opcionales dentro de `constraints`.
Se mantiene deliberadamente `arp.dictionary/v1` en preproducción: no se crea formato, versión, release,
alias ni capa transitoria. Los lectores anteriores rechazan las nuevas definiciones; los nuevos rechazan
los identificadores anteriores. No se promete compatibilidad en ninguna dirección.

Para conservar una capacidad previa se escriben ambos atributos explícitamente; por ejemplo, el antiguo
`INT16` se expresa como `type: INTEGER, constraints: {bits: 16, signed: true}`, conservando también sus
restricciones lógicas. Eliminar esos atributos puede inferir otra capacidad y no es una migración equivalente.
Los nombres de IDs y casos que contienen tamaños históricos son identidades de prueba, no alias de tipos.

Se actualizan esquema y catálogo de diccionario, descriptores, fuentes de fixtures, esquemas de observación
física y resultados de lectura, claves tipadas, LIST/GET, CREATE, UPDATE, DELETE y sus fixtures de registro,
menús y ciclo de vida. La lista de tipos reconocidos por la demo Angular también utiliza `INTEGER`.
Los nombres nativos SQL se conservan como observación opaca. La actualización de fixtures modulares no
introduce ninguna funcionalidad adicional de módulos o menús.

No se implementan tipos directos en CDS, autoridad `CDS`/`DATABASE`, creación de tablas, migraciones,
los cinco estados del borrador 1.0 ni ninguna otra propuesta de ese documento.
Se conservan la prueba de contención del dominio lógico completo, la autorización y las garantías de escritura;
no se habilitan escrituras usando solo la intersección de dominios incompatibles.
No se modifica código de runtimes PHP, Java o .NET, ni se incorporan referencias a aplicaciones consumidoras.

## Revisión del trabajo encontrado

La rama `feature/arp-integer-001` ya existía sobre `main` actualizado, con 16 archivos modificados y dos nuevos,
sin commits propios. Se revisó su diff y se ejecutaron las pruebas antes de reutilizarlo: **13 fallos y 5 errores**
en la primera ejecución, incluidos cinco módulos de pruebas que no podían importarse.

| Parte encontrada | Evaluación y decisión |
| --- | --- |
| Enum de tipos y capacidades explícitas | Útiles; se completa la migración en todos los perfiles activos. |
| Cadenas exactas y derivación central | Útiles; validación completada y contrastada con aritmética independiente. |
| Eliminación de `INTEGER_RANGES` | Correcta como objetivo; faltaba adaptar sus consumidores de lectura y escritura. |
| Inferencia con un solo extremo | Incompleta: no comprobaba ambos lados del dominio al promover tamaño. Corregida. |
| `bits: null` y `signed: null` | Se confundían con omisión en el helper. Ahora son inválidos. |
| Intervalos y `multipleOf` | Faltaba comprobar la existencia de múltiplos, también para negativos. Corregido. |
| Capacidad física sin límites | Afirmaba compatibilidad sin evidencia. Corregida a `not-verified`. |
| Pruebas y contadores | Describían el estado anterior. Adaptados conservando los antecedentes originales. |
| Documentación e impacto CRUD | Pendientes en el avance; completados tras esta revisión. |

También se fija capacidad antes del contexto, se validan semánticamente definiciones INTEGER antes de exponer
descriptores y se preserva el modelo matemático de metadatos numéricos de portabilidad 002.

## Casos y evidencia reproducible

El [boceto original](../proposals/integer/cases.json) y su esquema permanecen íntegros como antecedentes.
Ahora sus expectativas de inferencia y valores se ejecutan semánticamente en las pruebas; el esquema aislado
no es una segunda autoridad. La autoridad estructural es el
[esquema activo](../../schemas/dictionary/v1/dictionary.schema.json).
JSON Schema verifica estructura; el oráculo exacto comprueba capacidades, contradicciones y valores.

- [INTEGER](../../fixtures/dictionary/v1/integer.json): 46 definiciones y 55 valores; las ocho capacidades,
  límites adyacentes, inferencia parcial, signo explícito, exclusiones, intervalos vacíos, múltiplos, tipos inválidos,
  `null`, desbordamientos, normalización y errores ordenados.
- [Valores del diccionario](../../fixtures/dictionary/v1/values.json): 136 vectores; capacidades anteriores
  expresadas explícitamente y cobertura del máximo sin signo de 64 bits.
- [Compatibilidad](../../fixtures/cds/v1/compatibility.json): 21 casos estructurales, incluida evidencia ausente
  o parcial, capacidades lógicas distintas de la observación y restricciones contextuales.
- [Lectura CDS](../../fixtures/cds/read/v1/cases.json): 80 resoluciones y 11 casos de intake conservados;
  descriptores efectivos y observaciones migrados, sin reinterpretar un nombre nativo como capacidad.
- [LIST/GET](../../fixtures/cds/listget/v1/cases.json): 93 vectores, incluidos GET del máximo sin signo de 64 bits,
  rechazo de su sucesor antes de leer y ordenación exacta de sus dos valores superiores adyacentes.
- [Escritura](../../fixtures/crud/write/v1/cases.json): 117 vectores, incluidos CREATE, UPDATE y DELETE con PK
  sin signo de 64 bits, overflow, evidencia ligada a una clave adyacente y conflicto entre estados adyacentes.
  El [codec](../../fixtures/crud/write/v1/codec-cases.json) incluye nodos numéricos rechazados y valores exactos.
- [Regresiones independientes](../../tests/test_integer_semantics.py): enumeración de valores de 8 bits,
  transiciones de cada capacidad y existencia de múltiplos contrastada con enumeración de intervalos negativos
  y positivos. Las expectativas no se regeneran invocando al mismo resolutor que se pretende verificar.

Se reutilizan intactos los 25 casos SERVICES-001 y los 51 SERVICES-002, incluidos sus hashes de manifiesto.
Los nuevos casos de escritura añaden identidades INTEGER sin alterar las precondiciones, confirmaciones,
acceso, historial, resultados inciertos o límites atómicos de esos servicios.

Comandos ejecutados desde la raíz:

```bash
python3 -m unittest discover -s tests -q
python3 tools/check_documentation.py
python3 tools/check_contract.py
python3 tools/check_cds_draft.py
python3 tools/check_cds_compatibility_draft.py
python3 tools/check_services_draft.py
python3 tools/check_service_invocation_draft.py
python3 tools/check_cds_read_draft.py
python3 tools/check_modules_draft.py
python3 tools/check_menus_draft.py
python3 tools/check_cds_listget_draft.py
python3 tools/check_crud_write_draft.py
git diff --check
```

Resultados locales: **214 pruebas correctas**; los once verificadores documentales/contractuales, **PASS**;
**428 aserciones compartidas inventariadas** en el diccionario. También pasan 31 casos de módulos,
17 de ciclo de vida/cache y 35 de menús. El chequeo documental verifica enlaces y hashes históricos.
No hay formateador general configurado; se comprueban las reglas aplicables de `.editorconfig`, el JSON
y `git diff --check`, sin reformatear archivos ajenos. El cambio Angular es únicamente la lista reconocida de tipos;
no se ejecutó su build porque sus dependencias no están instaladas en este checkout.

Estos resultados son de herramientas de desarrollo y un oráculo finito en memoria, con Python 3.14 local.
No son pruebas SQL ni evidencia de conformidad de ningún runtime. Las observaciones de adaptadores siguen
siendo ilustrativas. La [evidencia histórica](../history/README.md), sus documentos, hashes y revisiones
permanecen intactos y no acreditan soporte del candidato INTEGER.

## Ajustes concretos que necesitará arp-php

1. Sustituir enums, listas de tipos, dispatch de validadores, modelos y descriptores por `INTEGER`, rechazando
   los siete identificadores anteriores. Mantener los IDs de elementos sin usarlos para deducir tipos.
2. Leer `constraints.bits` y `constraints.signed` con distinción entre omisión, `null`, booleanos y enteros
   matemáticos; aplicar exactamente el algoritmo de inferencia y publicar la capacidad resuelta.
   Validar la definición completa antes de activar el catálogo o exponer descriptores.
3. Separar dominio representable, intervalo lógico y `multipleOf`; implementar límites exclusivos y la
   prueba de existencia de múltiplos con división exacta también para negativos. Conservar códigos,
   orden de incidencias, normalización de `-0` y presupuestos de intake, sin conversiones permisivas.
4. Sustituir cualquier comparación o serialización que pase por `float`, y cualquier cast indiscriminado
   a `int`. El máximo sin signo de 64 bits supera `PHP_INT_MAX` incluso en PHP de 64 bits: elegir una
   estrategia exacta y acotada de cadenas decimales o aritmética de precisión suficiente para comparación,
   división, módulo, ordenación y normalización. No se impone una extensión PHP como parte del contrato.
5. Actualizar el adaptador MariaDB para publicar `scalarType: INTEGER` y límites exactos realmente observados,
   incluidos tipos sin signo. Conservar `nativeType` sin interpretarlo en el núcleo; distinguir evidencia
   parcial, incompatibilidad y contención demostrada. El proveedor debe devolver valores grandes sin pérdida
   y enlazarlos a parámetros SQL sin casts a flotante ni overflow de enteros nativos.
6. En el resolutor CDS, congelar capacidad antes del contexto; conservar restricciones intrínsecas y
   contextuales, materializar las efectivas y mantener la contención del dominio completo como precondición.
   No ampliar capacidad a partir de datos ni recortar dominios para habilitar escritura.
7. Migrar codecs de PK simple/compuesta, LIST/GET, referencias, cursores y resultados tipados a
   `{field, type: "INTEGER", value: "..."}`. Obtener capacidad del descriptor confiable; comparar,
   ordenar, detectar duplicados y normalizar claves exactamente, preservando claves ocultas y sus enlaces.
8. En CREATE, validar valores efectivos y defaults con su capacidad y restricciones; en UPDATE, validar
   enviados, baseline y confirmaciones sin redondear ni reescribir campos omitidos. En DELETE, preservar
   evidencia de lectura completa, propósito, generación, contexto y estado exacto, incluidos enteros grandes
   históricos. Rechazar desbordamientos y bindings obsoletos antes de escribir; conservar resultados inciertos.
9. Migrar definiciones y fixtures activos de arp-php con capacidad explícita cuando deba conservarse el
   dominio previo; ejecutar el nuevo inventario compartido y las obligaciones de proveedor sobre MariaDB
   real, incluidos los casos de 64 bits sin signo y barreras CRUD. Registrar evidencia nueva contra el commit
   adoptado: los resultados anteriores no sirven como conformidad de este cambio.

Esta lista es un traspaso de implementación; ninguno de esos cambios de runtime se ejecuta en esta PR.