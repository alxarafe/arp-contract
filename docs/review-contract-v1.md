# Revisión de docs/arp-contract-v1

**Estado:** propuesta para revisión, 21/11/2026. Sin fusión, etiquetas ni publicación de versiones.
**Base contrastada:** `eb38cb96e6ccd218734df2a181908de46067e0c7`.
El commit previo `0cd2573` añadió el archivo documental; no aprobó un contrato 1.0.

## Clasificación del diff pendiente

| Responsabilidad | Archivos | Evaluación |
| --- | --- | --- |
| Exclusión local | `.gitignore`: `private/` | No cambia el contrato; nada privado se incluye en Git. |
| Archivo documental | 24 documentos y sus copias | Se conservan las rutas originales. |
| Neutralidad documental | README, histórico y notas | Originales íntegros en Git. |
| Artefactos locales | Informes de paquetes ignorados por Git | No se incorporan a los commits ni a la PR. |
| Dirección funcional | Borradores y hoja de ruta | Propuestas pendientes de aprobación. |
| Contrato incompatible | `INTEGER`, `bits`, `signed` | Aislados del esquema vigente. |
| Límite de longitud | `10^128 - 1` frente a `10^128` | Regresión descartada. |
| Pruebas INTEGER | Estructura y compatibilidad | Sin verificación semántica de valores. |

## Compatibilidad de INTEGER

El diff original mantenía `apiVersion: arp.dictionary/v1` mientras rechazaba `INT8`, `UINT8`, `INT16`,
`UINT16`, `INT32`, `UINT32` e `INT64`. El catálogo y los ejemplos actuales contienen esos tipos.
La regresión inicial confirmó rechazos del catálogo y fallos derivados en LIST/GET y fuentes modulares;
no se cambian sus expectativas para hacerlos pasar. El esquema vigente se conserva idéntico a la base.
La propuesta tampoco es aceptada por lectores actuales: hay incompatibilidad en ambas direcciones.

No basta cambiar el nombre del tipo: `INT32` sin límites tiene un dominio concreto; inferir desde los límites
puede reducirlo o ampliarlo. Para conservar un dominio histórico habría que explicitar capacidad, signo,
límites y restricciones, y demostrar que descriptores y normalización siguen siendo equivalentes.
La propuesta añade capacidad de 64 bits sin signo, inexistente como identificador previo, que exigiría
representar exactamente hasta `18446744073709551615` en todos los adaptadores.

Impacto que requiere una decisión conjunta antes de adoptar:

- Identificador de formato y estrategia de ruptura: nuevo formato explícito o cambio deliberado documentado;
  no reinterpretar silenciosamente el mismo `apiVersion`. No se implementan alias ni conversiones aquí.
- Descriptores, fuente YAML/JSON, validación escalar, errores y límites de recursos del Data Dictionary.
- Physical Definition, Logical Definition, Projection, referencias tipadas y codec de LIST/GET y servicios.
- Catálogos, ejemplos y fixtures compartidos; adopción posterior e independiente de cada runtime y cliente.
- Inferencia con extremos ausentes/exclusivos, intervalos vacíos, `multipleOf`, signo y capacidad explícitos.
- Enteros exactos fuera de 53 bits, 64 bits sin signo, límites de hasta 64 bits y límites de recursos del parser.

El esquema aislado es un boceto estructural. Las siete definiciones semánticamente inválidas que acepta
se identifican expresamente en las pruebas; los resultados de inferencia y valores en `cases.json`
son expectativas propuestas **sin verificador semántico ni evidencia de conformidad**.
No se exige `INTEGER` a los contratos vigentes ni se modifica ningún runtime.

## Otras decisiones funcionales propuestas

El borrador también propone autoridad `CDS`/`DATABASE`, creación inicial de tablas desde definiciones,
tipos directos y cinco estados de compatibilidad física. No son cambios editoriales.
Su sintaxis, transición desde los estados existentes y capacidades de adaptador están pendientes.
La regla de aceptar un valor dentro de la intersección lógica/física debe contrastarse con el contrato
vigente de compatibilidad de definiciones; no lo sustituye esta documentación.
Las garantías existentes de UPDATE parcial, concurrencia, atomicidad y resultado incierto se mantienen.
La hoja de ruta no demuestra CRUD operativo. El trabajo de escritura queda pendiente de cerrar esta revisión.

## Conservación y referencias

El [índice histórico](history/2026-11-20-pre-v1.md) enlaza los originales en una revisión Git inmutable.
El [manifiesto](history/manifest.json) registra rutas y SHA-256 tanto originales como navegables.
Las copias navegables conservan las decisiones y evidencias técnicas; se generalizan identidades de
consumidores y se reparan enlaces a esquemas, fixtures y herramientas conservados en la raíz.
No se afirma identidad byte a byte después de esas correcciones. No se reescribe el historial Git.
Las rutas originales siguen como entradas hacia el archivo para evitar enlaces rotos.

La neutralidad afecta también al histórico navegable y a metadatos de procedencia, sin sustituir hashes
ni atribuir la procedencia original a otro repositorio. Los nombres originales se consultan en la revisión Git.
Los nombres de la plataforma, sus paquetes y sus repositorios propios no son aplicaciones consumidoras.

## Comprobaciones

Ejecución desde la raíz del repositorio, sin instalar dependencias generales nuevas:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_documentation.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_contract.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_cds_draft.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_cds_compatibility_draft.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_services_draft.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_service_invocation_draft.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_cds_read_draft.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_modules_draft.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_menus_draft.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_cds_listget_draft.py
git diff --check
```

El comprobador documental verifica destinos de enlaces locales, fragmentos Markdown, copias del histórico,
referencias locales a GitHub y hashes del manifiesto. Las URLs externas se inventarían por separado. La comprobación offline no solicita recursos por red.
No se ejecutan pruebas de MariaDB ni pruebas de conformidad de runtimes en esta revisión.

## Resultados registrados

- Pruebas de regresión: **187/187** correctas, con Python 3.14 local.
- Los nueve verificadores contractuales existentes: **PASS**.
- Referencias locales y a objetos Git: **214** verificadas; histórico: **25** documentos y hashes correctos.
- Las **17** URLs externas se inventariaron. Se recuperaron los diez documentos GitHub en sus revisiones
  exactas, confirmando los tres repositorios y las tres revisiones enlazadas. La especificación YAML
  externa también se abrió correctamente. No se reejecutaron las evidencias históricas enlazadas.
- `git diff --check`: correcto. `private/` está ignorada y sin archivos rastreados.
- El esquema vigente, ejemplos y fixtures históricos permanecen iguales a la revisión base.

CI recupera el historial Git para verificar los hashes de la revisión fuente; no necesita acceder
a las aplicaciones consumidoras. Estas comprobaciones no evalúan ningún runtime ni base de datos.