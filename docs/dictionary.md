# ARP 1.0 — Diccionario

**Propuesta incompatible pendiente de aprobación.** Este documento no sustituye `arp.dictionary/v1`.
El esquema vigente conserva los siete identificadores enteros históricos y sus fixtures.
La [revisión de compatibilidad](review-contract-v1.md) y el
[esquema aislado de INTEGER](proposals/integer/dictionary.schema.json) describen el cambio propuesto.
No se declara soporte de los runtimes ni se cambia ningún identificador de formato.

## Tipos

`BOOLEAN`, `STRING`, `TEXT`, `INTEGER`, `DECIMAL`, `UUID`, `DATE`, `TIME`, `DATETIME`, `ENUM`, `BINARY`.

El formato 1.0 propuesto usaría exclusivamente `INTEGER` para enteros. Los identificadores anteriores `INT8`, `UINT8`,
`INT16`, `UINT16`, `INT32`, `UINT32`, `INT64` no serían alias en la propuesta; siguen siendo válidos en el formato
vigente. Los elementos del diccionario son reutilizables, pero los campos CDS también podrán declarar un tipo
directamente.

## INTEGER

Las propiedades `minimum`, `maximum`, `bits` y `signed` se declaran dentro de `constraints`:

```yaml
apiVersion: arp.dictionary/v1
elements:
  - id: demo.score
    type: INTEGER
    constraints:
      minimum: '0'
      maximum: '100'
```

- `minimum` y `maximum`: enteros decimales exactos expresados como cadenas, inclusivos salvo `exclusiveMinimum` o
  `exclusiveMaximum`. Son límites de validación lógica.
- `signed`: booleano opcional. Si se declara, manda y debe ser compatible con los límites. Si se omite, vale `false`
  cuando `minimum` está declarado y es mayor o igual que cero; en otro caso vale `true`.
- `bits`: entero opcional entre `8`, `16`, `32` y `64`. Si se declara, fija la **capacidad lógica requerida** y debe
  cubrir los límites. No obliga a que exista un tipo nativo SQL de igual tamaño.
- Si se omite `bits` y se conocen ambos límites, se elige la menor capacidad de la lista que cubra el intervalo. Si
  falta cualquiera de los dos límites, se parte de 32 bits y solo se amplía a 64 cuando un límite declarado lo exige; no
  se reduce automáticamente por tener un único extremo.
- Si ningún tamaño de hasta 64 bits puede cubrir los límites, la definición es inválida. `UINT64` está permitido como
  capacidad abstracta y requiere aritmética exacta, aunque un runtime no disponga de un entero primitivo de 64 bits sin
  signo.
- Los valores válidos deben satisfacer simultáneamente el rango del tipo derivado, `minimum`/`maximum` y las demás
  restricciones aplicables. El rango del tipo no sustituye a las restricciones explícitas.
- `multipleOf` y los extremos exclusivos conservan su semántica actual. Para determinar si un intervalo entero cabe, los
  extremos exclusivos se ajustan al primer/último entero permitido. Un intervalo vacío es inválido.

Capacidad de un entero con `N` bits:

| `signed` | Rango representable |
| --- | --- |
| `true` | `-2^(N-1)` a `2^(N-1)-1` |
| `false` | `0` a `2^N-1` |

### Ejemplos

| Límites y atributos declarados | Capacidad derivada |
| --- | --- |
| `minimum: '0'`, `maximum: '100'` | UINT8 |
| `minimum: '-100'`, `maximum: '100'` | INT8 |
| `minimum: '0'`, `maximum: '100'`, `bits: 16` | UINT16 |
| `minimum: '0'`, `maximum: '100'`, `bits: 16`, `signed: true` | INT16 |
| `minimum: '0'`, `maximum: '200'`, `signed: true` | INT16 |
| `minimum: '0'`, `maximum: '1000'` | UINT16 |
| Sin límites ni atributos | INT32 |
| Solo `minimum: '0'` | UINT32 |
| Solo `maximum: '100'` | INT32 |

`bits: 8` con `minimum: '0'` y `maximum: '1000'` es inválido. También lo es `signed: false` con un mínimo negativo. Un
límite fuera del dominio representable es un error de definición, no un motivo para truncar, redondear ni saturar
valores.

## Reglas generales

1. El diccionario valida valores escalares y restricciones intrínsecas. Presencia, nulabilidad, identidad, claves,
   acceso y persistencia pertenecen a CDS y al anfitrión.
2. Las definiciones aceptan únicamente las propiedades de su tipo; las propiedades desconocidas son errores.
3. Las comparaciones numéricas y la normalización son exactas. El formato neutral para enteros es una cadena decimal
   canónica; no se obliga a cada lenguaje a usar cadenas internamente.
4. `INTEGER` es independiente de la representación física. El adaptador SQL debe demostrar que el tipo elegido admite
   los valores exigidos; si no puede hacerlo, no habilita escrituras inseguras.
5. La documentación histórica está en `docs/history/`. La adopción de estas reglas y la política de transición están
   pendientes; el esquema vigente no se modifica.