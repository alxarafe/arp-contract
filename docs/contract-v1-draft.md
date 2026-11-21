# ARP — Contrato funcional 1.0

**Borrador no activado como conjunto.** Solo INTEGER se incorpora al candidato activo mediante
[ARP-INTEGER-001](features/arp-integer-001.md) y la [especificación definitiva](dictionary.md), que prevalece
sobre la sección 2. El [boceto original](proposals/integer/dictionary.schema.json) se conserva como antecedente.
Las demás propuestas de este documento permanecen pendientes. No se publica versión ni se modifica un runtime.

**Borrador para revisión.** No es una versión publicada ni declara conformidad de PHP, Java o .NET.

## 1. Objetivo

ARP proporciona tipos abstractos, modelos CDS, proyecciones, validación, operaciones CRUD y metadatos neutrales para
clientes. La aplicación conserva los datos, la lógica de negocio, los permisos y el control de despliegue. El
diccionario podrá utilizarse sin base de datos ni cliente gráfico.

## 2. Tipos

Tipos previstos: `BOOLEAN`, `STRING`, `TEXT`, `INTEGER`, `DECIMAL`, `UUID`, `DATE`, `TIME`, `DATETIME`, `ENUM` y
`BINARY`.

`INTEGER` sustituye los siete tipos enteros anteriores en el candidato activo, sin alias. La sintaxis,
inferencia, capacidades, límites exclusivos, `multipleOf`, errores y representaciones exactas se definen en
[Diccionario e INTEGER](dictionary.md). Esta incorporación independiente no aprueba las secciones siguientes.

## 3. CDS y persistencia

Se propone que cada entidad persistente declare una autoridad (sintaxis y efectos pendientes):

- `CDS`: el modelo declarativo especifica el esquema deseado; el adaptador puede crear tablas nuevas.
- `DATABASE`: la base de datos existente gobierna su esquema; ARP lo observa y lo vincula al modelo lógico.

Los campos CDS podrán reutilizar elementos del diccionario. También se prevé declarar tipos escalares directamente, con
la misma semántica de validación; su representación exacta en YAML/JSON debe cerrarse antes de actualizar los esquemas.

Se propone incorporar creación **inicial** de tablas desde CDS, clave primaria, nulabilidad, tipos, restricciones e
índices indispensables. No incluye migraciones de datos ni cambios automáticos sobre tablas existentes. La carga de
documentos no modifica por sí misma una base de datos.

## 4. Compatibilidad física y estados

La compatibilidad se verifica con el esquema realmente observado. Cada entidad mantiene uno de estos estados:

| Estado | Significado |
| --- | --- |
| `OPTIMO` | El almacenamiento usa la capacidad pedida, o la representación más ajustada disponible en ese motor. |
| `SINCRONIZADO` | Satisface el CDS, aunque con capacidad física superior a la necesaria. |
| `DESALINEADO` | Hay diferencias y solo se habilitan operaciones cuya seguridad pueda demostrarse. |
| `INCOMPATIBLE` | No se pueden garantizar requisitos de alguna operación necesaria. |
| `NO_VERIFICADO` | Falta evidencia suficiente para afirmar compatibilidad. |

Una divergencia no bloquea por sí sola todas las operaciones. Para escritura se exige que el valor pertenezca tanto al
dominio permitido por CDS como al dominio físico **verificado**, incluidas restricciones reales de la base de datos. El
backend es la autoridad final.

Ejemplo: CDS pasa de `0..100` a `0..1000` y el campo físico continúa siendo `TINYINT UNSIGNED` sin otra restricción. Se
admiten valores de `0` a `255`; `101` es válido, `256` se rechaza hasta ampliar la estructura. El estado es
`DESALINEADO`. Si existiese una restricción SQL `CHECK` adicional, también debe respetarse; el MVP no generará
automáticamente un `CHECK` desde cada límite lógico.

## 5. Proyecciones y permisos

Una proyección declara campos expuestos y operaciones candidatas (`LIST`, `GET`, `CREATE`, `UPDATE`, `DELETE`). A partir
de ella, el backend resuelve una **proyección efectiva** según usuario y contexto. Una proyección declarada nunca
concede autorización por sí sola.

El primer CRUD gestionado opera sobre **una sola entidad persistente y una clave inequívoca**. No incluye joins
modificables. La proyección efectiva debe impedir exponer, consultar o modificar campos no autorizados, incluso mediante
solicitudes manipuladas.

## 6. CRUD gestionado

- `LIST` y `GET`: reutilizar los mecanismos existentes de lectura verificada, proyección y acceso autorizado.
- `CREATE`: validar campos presentes, valores obligatorios, nulabilidad, unicidad y dominio efectivo antes de insertar.
- `UPDATE`: modificación parcial; un campo omitido permanece inalterado. Un `null` explícito es distinto de ausencia.
  Validar cada campo enviado, incluso si no cambia; escribir únicamente diferencias efectivas.
- **Concurrencia de UPDATE:** contrastar los valores originales relevantes con los actuales bajo protección
  transaccional o garantía equivalente; un conflicto no produce escrituras parciales. No sobrescribir silenciosamente
  cambios ajenos.
- `DELETE`: exigir identidad, autorización y protección contra borrados concurrentes; concretar la política exacta antes
  de implementarlo.

Los servicios empresariales pueden delegar operaciones a manejadores de la aplicación sin que ARP invente reglas de
dominio.

## 7. Cliente y errores

El backend publica metadatos suficientes para generar listas y formularios: identidad de proyección, campos visibles,
tipos, restricciones efectivas, capacidades, editabilidad y estado físico. Angular no necesita conocer tablas SQL ni el
lenguaje del servidor.

Las solicitudes envían valores y precondiciones de modificación, **no permisos ni contexto confiable**. El backend
devuelve resultados tipados y errores estructurados con códigos estables, detalle de campo autorizado y mensajes
localizables. El idioma afecta a la presentación, no a la identidad de tipos, campos o errores.

## 8. Alcance de ejecución

1. Aprobar esquema, ejemplos y pruebas contractuales.
2. Implementar `arp-php` con MariaDB y demostrarlo en `arp-php-test`.
3. Consumir el mismo contrato desde el Angular existente.
4. Adaptar `arp-java` y `arp-dotnet` con las mismas pruebas de conformidad.

No se publicarán versiones ni se introducirán alias transitorios por este trabajo. Las migraciones y el CRUD sobre joins
se estudiarán después del primer CRUD funcional.

## 9. Decisiones aún necesarias antes de aprobar 1.0

- INTEGER queda cerrado por ARP-INTEGER-001; las demás decisiones de esta lista continúan pendientes.
- Sintaxis precisa para tipos directos, referencias al diccionario, claves, valores por defecto y restricciones CDS.
- Contrato concreto de metadatos, transporte, serialización y representación de errores.
- Precondiciones y resultado de DELETE, generación de identificadores y prueba de operaciones atómicas.

Los JSON Schemas y los vectores de pruebas son la fuente verificable de sintaxis y resultados; este texto solo fija las
reglas funcionales. Las discusiones y especificaciones anteriores se conservarán en `docs/history`.