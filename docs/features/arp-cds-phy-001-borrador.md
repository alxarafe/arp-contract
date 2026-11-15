# ARP-CDS-PHY-001 — Contrato candidato de descripción física regenerable

**Estado:** PROPUESTA TÉCNICA PARA REVISIÓN. No aprobada, no publicada y sin soporte declarado en ningún runtime.
**Ámbito:** primer paso contractual del recorrido CDS–Angular, aprobado funcionalmente como D01, D04 y D11 en `docs/ARP_CDS_acuerdos_aprobados_2026-11-15.md`.
**Compatibilidad:** no altera `ARP-DICT-001`; no introduce API HTTP, tablas en ARP ni un ORM propio. `arp-res-001-borrador-especificacion.md` sigue siendo antecedente no aprobado y **no** se toma como contrato del modelo lógico CDS.

## 1. Decisiones funcionales que NO se reabren

1. La base de datos real es la autoridad del almacenamiento existente. ARP **genera** una definición física por tabla o vista cuando se necesita, si aún no está en caché.
2. El artefacto generado **no se personaliza**. Todas las especializaciones del consumidor (referencias al diccionario, etiquetas, rangos 0…10, etc.) pertenecen al YAML lógico separado.
3. Una migración controlada **invalida explícitamente** la definición física afectada; en el próximo uso se vuelve a generar. No se requiere vigilancia continua de cambios DDL ni introspección general en cada arranque.
4. La invalidación alcanza instantáneas lógicas y proyecciones compiladas dependientes. Nunca se borran YAML lógicos ni proyecciones del usuario.
5. Las tablas físicas que permanecen en la base de datos pueden existir aunque su módulo esté desactivado; ello **no publica** servicios ni proyecciones de ese módulo.
6. El modelo lógico efectivo podrá incorporar automáticamente una nueva columna física. Ninguna proyección pública incorpora nuevos campos sin una declaración explícita.
7. El mismo significado contractual se podrá implementar con PostgreSQL (Java/.NET) y MariaDB (PHP), mediante adaptadores independientes.

## 2. Alcance de este primer contrato candidato

Define la **forma de una instantánea física** que el adaptador puede producir y recuperar de una caché, junto con pruebas de estructura y algunas reglas de consistencia. Se propone un documento `arp.physical/v1` por objeto físico. Su archivo puede contenerse en una caché persistente YAML; ni su ruta ni el formato serializado son fuente de verdad por delante de la BD.

La generación efectiva por introspección, la invalidación entre procesos y la conexión con el modelo lógico se especificarán y probarán en pasos sucesivos; **no están implementadas** por los archivos de esta propuesta.

El documento contiene:

- `sourceId`: identidad estable del origen de almacenamiento, declarada por la aplicación/proveedor; no equivale a un usuario ni a un permiso.
- `object`: identidad física (`catalog` y/o `schema` cuando correspondan, `name`, `kind: TABLE|VIEW`).
- `columns`: nombre físico, ordinal, tipo nativo y **únicamente** capacidades conocidas por el adaptador (nulabilidad, longitud con unidad, rango entero, precisión y escala). También puede indicar si la columna es generada o de identidad, cuando se ha verificado.
- `primaryKey`, `indexes` y `foreignKeys` **opcionales** cuando el proveedor conoce dichos datos de forma suficiente. Su omisión **no implica** que no existan; la lista vacía sí comunica que se ha observado que no hay entradas de esa clase.

**Propiedad ausente ≠ `false`, `0`, `[]` ni capacidad ilimitada.** En particular, la ausencia de `nullable` representa información no verificada, **no** `nullable: false`. El contrato de compatibilidad físico↔lógico tendrá que respetar esta distinción.

Los rangos enteros se expresan como cadenas decimales exactas y no como números de punto flotante. Por ejemplo, MariaDB `TINYINT SIGNED` puede publicar `-128…127` y PostgreSQL `smallint` `-32768…32767`, si el adaptador ha identificado esas capacidades con certeza. Una columna `VARCHAR(10)` puede publicar una longitud 10 en `CHARACTERS` o en `BYTES` **solo cuando conoce realmente la unidad**. No se supondrá equivalencia entre ambas.

Las claves, relaciones y los índices son **metadatos del almacenamiento**, no autorizaciones de lectura/escritura ni asociaciones semánticas del CDS. Una vista SQL no es lo mismo que una proyección ARP.

## 3. Ejemplo de representación candidata

```yaml
apiVersion: arp.physical/v1
sourceId: demo.mariadb
object:
  schema: demo
  name: evaluaciones
  kind: TABLE
columns:
  - name: id
    ordinal: 1
    nativeType: bigint
    nullable: false
    identity: true
  - name: puntuacion
    ordinal: 2
    nativeType: tinyint
    nullable: false
    integerRange:
      minimum: '-128'
      maximum: '127'
  - name: codigo
    ordinal: 3
    nativeType: varchar
    characterLength:
      value: 10
      unit: CHARACTERS
primaryKey: [id]
```

Es **solo una propuesta de formato**. El usuario ya aprobó las capas y el ciclo de vida, **no esta gramática ni estos identificadores**. El documento `fixtures/physical/v1/example.mariadb.yaml` contiene el ejemplo verificable correspondiente.

## 4. Reglas semánticas a especificar y comprobar

1. La identidad física completa se compone de `sourceId` y de la identidad del objeto: nombres y esquema/catálogo según el motor. El proveedor debe resolver nombres ambiguos sin adivinar el esquema.
2. No puede haber dos columnas con el mismo nombre canónico **según la política de nombres del proveedor**, ni dos ordinales iguales. El modelo portable conserva el nombre original; no se aplica case folding global.
3. Si se declara `primaryKey`, todos sus nombres deben existir en `columns` y no repetirse. Un array omitido equivale a no observado; un array vacío no es una clave primaria válida.
4. Si se declaran índices o claves externas, todas sus referencias locales tienen que apuntar a columnas existentes y estar libres de duplicados; las referencias externas requieren nombres de destino explícitos. No se exige que todo proveedor pueda reconstruir toda expresión de índice o relación.
5. `integerRange.minimum` ≤ `integerRange.maximum`; `decimalGeometry.scale` ≤ `decimalGeometry.precision`. No se declara un rango o precisión que el proveedor no haya comprobado realmente.
6. No se infiere `nullable`, restricciones de negocio, etiquetas, valores por defecto funcionales, permisos, recursos HTTP o operaciones CRUD a partir del nombre/tipo de la columna.
7. No se aplican autocorrecciones de valores ni cambios de esquema SQL al leer un YAML físico.
8. Una definición cacheada solo se considera vigente bajo el **protocolo de invalidación del consumidor**. El contrato no puede garantizar detectar cambios DDL externos no comunicados.

Los casos de prueba candidatos comprueban la **forma** y coherencia local, no la veracidad de los datos frente a una BD. Esa evidencia solo podrá aportar una prueba de adaptador e introspección real.

## 5. Política de caché e invalidación

- **Cache miss:** el runtime solicita al adaptador la descripción actual del objeto, la valida y publica una instantánea completa; si la inspección falla, no publica un artefacto incompleto.
- **Cache hit:** se usa la instantánea disponible, sin exigir conexión SQL por cada lectura, siempre bajo la suposición documentada de que las migraciones invalidan la caché correctamente.
- **Migración confirmada:** la aplicación invalida el objeto y todos sus derivados lógicos/de proyección; la siguiente consulta debe obtener una nueva generación.
- **DDL externo:** el administrador debe solicitar invalidación manual. No prometer detección autónoma.
- **Desactivación de módulo:** afecta al catálogo público activo, **no** borra objetos SQL, archivos físicos ni personalizaciones lógicas.
- **Concurrencia/múltiples instancias:** debe garantizarse que no se observa una mezcla incoherente de generaciones. El protocolo distribuido y su token de generación quedan pendientes de contrato posterior.

**Riesgo reconocido:** borrar solamente el archivo YAML no es suficiente si existen cachés de proceso. La invalidación **debe ser una operación del sistema**, capaz de borrar artefactos y notificar a los catálogos dependientes; la eliminación del archivo es un posible mecanismo interno, no la interfaz pública del contrato.

## 6. Alcance de las pruebas incluidas

El paquete contiene:

- `schemas/physical/v1/physical.schema.json`: JSON Schema Draft 2020-12 candidato de un documento físico.
- `fixtures/physical/v1/cases.json`: 13 casos (válidos, defectos estructurales y defectos semánticos locales) con resultado esperado.
- `fixtures/physical/v1/example.mariadb.yaml`: ejemplo legible de generación física.
- `tests/test_physical_candidate.py`: pruebas de integridad sobre esquema, fixtures y ejemplo YAML.

Para ejecutar este conjunto candidato desde la raíz de `arp-contract`:

```bash
python3 -m unittest discover -s tests -p 'test_physical_candidate.py' -v
```

Requiere `jsonschema` y `PyYAML`, ya utilizados por las herramientas de desarrollo del contrato. **Superar estas pruebas NO acredita introspección real, compatibilidad física-lógica, invalidación ni conformidad de Java/.NET/PHP.**

## 7. Siguientes contratos y cuestiones abiertas

1. `ARP-CDS-LOG-001`: especialización YAML persistente sobre el modelo físico, enlace con `ARP-DICT-001`, y composición estricta de rangos/tipos; incorporación automática de nuevas columnas sin modificar YAML del consumidor.
2. `ARP-CDS-PRJ-001`: proyecciones públicas explícitas, derivación sin ampliación de campos, restricciones no debilitables y metadatos de presentación modificables.
3. `ARP-CDS-OPS-001`: operaciones declaradas; CRUD automático **solo** sobre tabla simple con clave y adaptadores; ejecución delegada para lógica específica.
4. `ARP-CDS-API-001`: contrato de exposición, metadatos de Angular y cinco familias de errores normalizados.
5. Integración y conformidad: introspección e invalidación real (PostgreSQL, MariaDB), demos Java/.NET/PHP y cliente Angular único.

**Por decidir al revisar esta propuesta:** forma exacta de identidades `catalog/schema` para los dos motores; perfil portable YAML aplicable; cómo demostrar que `nullable`, longitud y límites son *verificados*; soporte inicial de índices y claves externas (representación disponible, cobertura real opcional); cómo se invalidan instantáneas entre procesos; si `arp.physical/v1` es el nombre adecuado. Ninguna de estas opciones es un acuerdo adicional de producto hasta su revisión.
