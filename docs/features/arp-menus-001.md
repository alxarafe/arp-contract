# ARP-MENUS-001 — Menús manuales y aportaciones modulares

**Estado:** candidato inicial para revisión; no normativo, integrado ni publicado. **Fecha:** 2026-11-17.
Base: [arquitectura](../architecture.md), [MODULES-001](arp-modules-001.md),
[CDS-READ-001](arp-cds-read-001.md), [SERVICES-001](arp-services-001.md) y [SERVICES-002](arp-services-002.md).
Define navegación funcional, no ejecución de operaciones, pantallas ni un sistema de permisos.

## 1. Ámbitos y fuentes

Una aplicación puede definir todos sus menús manualmente, recibir aportaciones de módulos o combinar ambos
mecanismos. Ningún modelo, proyección, CRUD o módulo genera entradas por defecto. Un módulo puede aportar
definiciones sin menú; la aplicación puede tener menús sin módulos.

Se contemplan inicialmente ámbitos **primary, secondary, contextual y system**, abiertos a otros nombres como
workspace. `scope` clasifica finalidad; **no** representa un slot visual, número de menús, ruta Angular o posición.
Puede haber cero o varios menús del mismo ámbito. Cada tema Angular decide libremente cuáles representa y dónde:
no reescribe las definiciones funcionales ni exige variantes, plantillas o sidebars en este contrato.

El candidato [menu-source.schema.json](../../schemas/menus/v1/menu-source.schema.json) representa una fuente
`arp.menu/v1` con `menus` y/o `contributions`. Se entrega por el mismo registro de proveedores de MODULES-001;
no existe ruta de paquete obligatoria ni descubrimiento por el nombre del archivo.

```json
{"apiVersion":"arp.menu/v1","contributions":[{"menu":"app.primary","entries":[
  {"id":"catalog.articles","parent":"app.business","order":10,"labelKey":"catalog.menu.articles",
   "destination":{"kind":"projection","target":"catalog.articles.public","operation":"LIST"}}
]}]}
```

`menus` declara `id`, `scope` y `entries`; `contributions` añade entradas a un menú declarado activo. Varios módulos
y la aplicación pueden aportar al mismo menú. Hay una única declaración de cada menú; una segunda declaración
no “gana”, aunque sea idéntica. Una contribución cuyo menú no existe es error; no crea un menú implícito.

Son admisibles las fuentes vacías: `{"apiVersion":"arp.menu/v1"}` y la misma fuente con `menus: []` y/o
`contributions: []` no aportan menús ni entradas. El esquema no exige contenido mínimo además de apiVersion.
No se crean menús por defecto. Declarar un menú con `entries: []` es distinto: el menú existe, aunque su árbol esté
vacío y el tema no lo represente. Una contribución con `entries: []` sigue referenciando un menú que debe existir
y cuyo propietario debe respetar MODULES-001; estar vacía no excusa esa referencia o dependencia.

## 2. Entradas, jerarquía y destino

Cada entrada tiene ID estable, único **dentro del menú**, `label` literal o `labelKey` —exactamente uno—, `parent`
opcional (nulo/ausente indica raíz), `order` entero opcional (0 por defecto) y destino opcional. Un ID puede repetirse
en otro menú sin colisión. Los IDs son sensibles a mayúsculas; no son rutas ni se regeneran según idioma o posición.
El padre pertenece al mismo menú. Se rechazan padres ausentes, autoreferencias y ciclos; no se promueven huérfanos.
Los hermanos se ordenan por `order` y después ID con comparación Unicode escalar, independiente de carga e idioma.
El perfil limita order a ±1000000, 4096 entradas activas totales y 64 niveles; etiquetas/IDs tienen los límites
explícitos de los esquemas candidatos. No se ordena por texto traducido ni se cambia el ID al traducir.

Una entrada sin destino es un grupo. Los grupos vacíos tras componer/filtrar no se incluyen en el resultado de
navegación; se conservan en la fuente autorada. Una entrada con destino puede tener hijos. Los hijos no heredan
permisos de ejecución ni ejecutan el destino del padre.

`destination` tiene `kind`, `target` y, cuando corresponda, `operation`. Siempre referencia un registro del host,
no código, SQL, nombres de clases ni una URL ejecutable recibida del cliente. El perfil comprueba:

- `projection`: proyección activa resuelta por CDS; operación obligatoria y declarada en esa proyección. Una
  operación ausente de su declaración es error de definición (`MENUS_OPERATION_UNAVAILABLE`).
- El host distingue **disponibilidad de ejecución y autorización por cada par proyección/operación**. Aunque
  LIST y GET estén declarados, puede permitir LIST y denegar GET, o tener GET autorizado pero no disponible en el
  servidor. En esos casos no se expone esa entrada ni sus descendientes; no se concede acceso a toda la proyección.
- Otros tipos —por ejemplo route—: un adaptador de destino registrado por el host valida nombre y contrato.
  Los fixtures usan destinos route locales preaprobados; no fijan rutas HTTP o Angular.
- Tipo no soportado o destino ausente: error de definición; no se inventa un enlace.

Esto no genera CRUD, un YAML obligatorio de servicio ni una correspondencia definitiva entre servicio y proyección.
**El servidor comprueba autoritativamente la operación al invocarla**, incluidos registro activo, disponibilidad,
autorización y controles de filas/campos de su contrato, aunque la entrada fuese visible o se envíe una petición
directa. Un menú o una selección del tema nunca es un permiso. El arnés usa `projectionAccess` para decisiones
separadas available/authorized por operación; no implementa un servicio ejecutable ni un sistema de permisos.
Esas decisiones forman parte de la evidencia de contexto de caché y no se reutilizan desde un contexto obsoleto.
Una etiqueta localizada se resuelve por un mecanismo del host; `labelKey` no define un formato I18N nuevo ni fuerza
a cargar traducciones dentro del renderer. La caché de etiquetas resueltas depende de locale/fuentes pertinentes.

### 2.1 Un menú principal, varias regiones visuales

Ejemplo funcional con dos opciones principales, incluido en los fixtures:

```text
app.primary (scope: primary)
├── app.catalog — Catálogo
│   └── catalog.articles — Artículos → catalog.articles.public / LIST
└── app.reports — Informes
    └── reports.summary — Resumen → reports.articles.summary / LIST
```

Un tema puede representar Catálogo e Informes como navegación principal y mostrar los descendientes de la opción
seleccionada como navegación secundaria visual. Seleccionar Catálogo muestra Artículos; seleccionar Informes muestra
Resumen. Otro tema puede mostrar todo el mismo árbol desplegado. Ambos consumen la misma jerarquía autorizada,
con los mismos IDs, orden, etiquetas y destinos: no se añade otra fuente, menú funcional o ámbito secondary.
“Secundaria” describe aquí una región de presentación, no el `scope: secondary` de otro menú independiente.

La selección es estado transitorio de presentación del tema; no una propiedad nueva de la definición ni un formato
de configuración ARP. Seleccionar un grupo no ejecuta una operación. Si una opción deja de estar disponible, el tema
descarta esa selección o elige otra existente, sin inventar descendientes ni recuperar entradas ocultas. Este ejemplo
no define slots, rutas de componentes, plantillas ni variantes; la distribución visual sigue siendo libre.

### 2.2 Límite actual del ámbito contextual

`scope: contextual` solo clasifica un menú de entradas declaradas y destinos registrados. El perfil **no implementa
selección de registros, vinculación a una fila, acciones dinámicas ni evaluación de condiciones visuales**. No hay
recordKey, condition o dynamicActions en la gramática; los fixtures rechazan esos campos en una entrada.
Las decisiones confiables de disponibilidad/autorización del host no son expresiones visuales evaluadas por ARP.
Se necesitaría otro contrato para aportar contexto de registro o acciones calculadas; este candidato no lo anticipa.

## 3. Personalización explícita de la aplicación

La aplicación aporta más entradas mediante una fuente normal o una composición explícita
[arp.menu-composition/v1](../../schemas/menus/v1/composition.schema.json). Cada edición identifica menú/entrada,
puede cambiar `order`, `parent`, `label`/`labelKey` y destino, o excluir la entrada. No renombra IDs, cambia un modelo
ni amplía una proyección. Cambiar destino requiere la misma validación y autorización del destino final.
Poner destino nulo convierte la entrada en grupo; cambiar label a literal sustituye labelKey, y viceversa.

`whenMissing` por defecto es error. La opción explícita ignore conserva una personalización de una entrada modular
ausente sin crearla: al reactivar el módulo se aplica de nuevo. Un error de esquema o dos ediciones de la misma
entrada siguen siendo errores aunque se indiquen como opcionales. No hay último escritor ni reparación silenciosa.
Una entrada propia de la aplicación dirigida a una proyección desactivada no se elimina automáticamente para
aceptar el plan; el host debe suministrar una configuración coherente.

Orden de composición, determinista y sin publicación parcial:

1. Seleccionar fuentes activas. Declarar menús; reunir aportaciones sin sobreescribir IDs.
2. Rechazar duplicados y dependencias obligatorias no declaradas antes de personalizar. Una exclusión o edición
   no oculta un conflicto de propiedad ni una dependencia incumplida de la aportación original.
3. Aplicar ediciones explícitas. Validar jerarquía, profundidad y destinos del conjunto activo completo.
4. Excluir entradas y sus subárboles. Reparentar expresamente antes de excluir permite conservar un hijo fuera.
5. Aplicar las decisiones confiables de visibilidad; retirar también descendientes de una entrada no disponible.
6. Podar grupos vacíos y ordenar. Publicar la composición completa solo con la generación/contexto vigentes.

Las exclusiones no excusan un destino inválido del conjunto activo; una edición puede corregirlo explícitamente.
No hay sistema propio de roles, expresiones de permisos, filtros arbitrarios ni ejecución del destino al componer.
El host puede suministrar destinos públicos sin identidad o decisiones por contexto. Los permisos de entrada del
arnés son datos privados de prueba, nunca autoridad aportada por el cliente.

## 4. Activación, caché y presentación

Retirar reports retira su aportación al menú compartido y su proyección; catalog permanece. Retirar ambos deja el
menú manual y no borra fuentes ni datos. Reactivar revalida referencias y reaplica personalizaciones conservadas.
El plan de módulos no se publica si la nueva composición produce referencias ausentes o conflictos.

Los menús y etiquetas derivados pertenecen a **la caché general de la aplicación**, no a cachés aisladas por módulo.
El artefacto depende de todas sus aportaciones, selección/membresía del menú, destinos resueltos, composición propia
y contexto relevante. Una aportación recién activada invalida el menú ya cacheado, incluso si antes no conocía ese
módulo. Cambiar solo traducciones puede conservar el árbol con labelKey e invalidar únicamente etiquetas resueltas.
Una personalización de un menú no obliga a invalidar otro cuya composición/dependencias no cambien.
Un cambio de política invalida vistas de ese contexto, conservando modelos ajenos a ella. No se reutiliza un menú
con permisos/contexto antiguos ni se comparte entre aplicaciones. MODULES-001 fija la barrera de publicación y
el criterio conservador cuando las dependencias no estén demostradas; no se especifica aquí un backend de caché.

El resultado de conformidad es `{valid:true,issues:[],menus:[...]}` con menús ordenados por ID y entradas anidadas
en `children`, sin `parent`. Conserva ID, ámbito, etiqueta/clave, orden y destino; no incluye procedencia privada.
Un menú declarado puede resultar vacío, sin forzar al tema a mostrarlo.
Fallo: `{valid:false,issues:[{family,code,at}]}`,
sin árbol parcial nuevo. Son resultados de composición, no resultados de invocar un servicio SERVICES-002.
Los códigos MENUS_* identifican conflictos, referencias, ciclos/límites, ediciones o destinos inválidos; pertenecen
a definition-invalid. Errores de un consumidor previo conservan su familia. Los textos y el transporte no se fijan.

## 5. Fixtures, límites y revisión

[Escenario compartido](../../fixtures/modules/v1/scenario.json), [vectores de menú](../../fixtures/menus/v1/cases.json),
[transiciones/caché](../../fixtures/modules/v1/transitions.json), [verificador](../../tools/check_menus_draft.py)
y [regresiones](../../tests/test_menus_draft.py). catalog y reports aportan al mismo menú manual; reports usa una
proyección derivada de catalog. Se comprueban personalización, jerarquía, conflictos, desactivación, visibilidad,
ámbitos abiertos, ausencia de generación automática y selección para invalidación de caché. La revisión incorpora
fuentes vacías, una jerarquía de dos opciones principales, decisiones LIST/GET independientes y límites contextuales.

Los fixtures guardan expectativas explícitas, independientes del resultado del oráculo. Las decisiones del host,
payloads de traducción/extensión, nombres de artefactos y grafos de caché son instrumentación privada: no otra
gramática de permisos, paquetes, traducciones o almacenamiento. Los esquemas de módulo/menú/composición son
candidatos nuevos para revisión; las gramáticas DICT/CDS y SERVICES existentes permanecen intactas.
No se acreditan runtimes, seguridad real, concurrencia, renderizado Angular ni almacenamiento a partir de estos tests.
No se implementa instalador, gestor visual, plantillas, variantes de temas, SQL, endpoints ni operaciones nuevas.