# ARP-MODULES-001 — Composición de módulos y fuentes

**Estado:** candidato inicial para revisión; no normativo, integrado ni publicado. **Fecha:** 2026-11-17.
Base: [arquitectura](../architecture.md),
[D01–D11](../decisions/ARP_CDS_modelo_semantico_primera_integracion_Angular.md),
[DICT-001](arp-dict-001.md), [CDS-READ-001](arp-cds-read-001.md) y [MENUS-001](arp-menus-001.md).
No modifica el borrador independiente LIST/GET ni depende de él.

## 1. Responsabilidad y registro

La aplicación registra módulos por **identidad estable, sensible a mayúsculas**, dependencias obligatorias y
aportaciones de fuentes. Identidad no significa paquete, directorio, clase, tabla ni ruta de instalación. El registro
confiable distingue propietario aplicación/módulo y conserva procedencia; no se deduce del contenido de un archivo.
La aplicación puede aportar definiciones propias con el mismo mecanismo que los módulos.

Un módulo puede aportar diccionario, modelos lógicos, proyecciones, traducciones, menús y futuros tipos registrados.
El perfil candidato [module.schema.json](../../../../../schemas/modules/v1/module.schema.json) representa ese registro
en memoria o YAML/JSON: `apiVersion: arp.module/v1`, `id`, `dependencies`, `sources`. No exige un archivo module.yaml.

```json
{"apiVersion":"arp.module/v1","id":"reports","dependencies":["catalog"],"sources":[]}
```

Cada fuente lleva `providerId`, `sourceId`, `kind`, `revision` y `handle`. El par proveedor/fuente identifica una
instantánea; `handle` es una referencia opaca al proveedor registrado, **no una ruta que ARP deba abrir**. `revision`
es evidencia de vigencia del anfitrión; no una versión negociada ni un selector de paquetes. Todo cambio semántico
de fuente debe cambiar su evidencia; el arnés usa además una huella del payload para comprobar invalidación.
Versiones de distribución, restricciones de versiones, instalación y descarga quedan fuera de este corte.

Solo un procesador registrado acepta cada `kind`; valida su formato y referencias antes de publicar. Los tipos
nuevos no requieren añadir columnas al módulo, pero tampoco se ignoran si están activos y falta su procesador.
Los payloads DICT/CDS conservan sus gramáticas y validadores. Traducciones y `custom.note` de los fixtures usan
procesadores ilustrativos: **no** establecen un formato de traducciones ni ejecutan plugins por nombre.
Una observación física procede del proveedor real del host, nunca se convierte en autoría empresarial del módulo.

## 2. Dependencias y activación

El anfitrión solicita el **conjunto activo completo**. No hay instalación, descubrimiento, activación transitiva o
cascada de desactivación implícitos. Un módulo activo exige que cada dependencia esté registrada y también activa.
Se rechazan IDs duplicados, activaciones repetidas, referencias ausentes y ciclos del grafo solicitado.
Los módulos inactivos no aportan fuentes ni necesitan cargar sus payloads/procesadores; sus metadatos de registro
sí conservan una identidad inequívoca. Las dependencias de un módulo inactivo se comprueban al intentar activarlo.
Se ordena topológicamente, desempate por ID Unicode escalar; ese orden **no** crea precedencia entre definiciones.

`reports` depende de `catalog`: activar solo reports se rechaza. Desactivar catalog manteniendo reports también.
Para retirar ambos se solicita explícitamente el conjunto sin ellos. Desactivar reports permite conservar catalog.
Las referencias obligatorias entre definiciones se validan además del grafo de módulos. Si una definición de A
referencia una definición cuyo propietario registrado es B, y ambos son módulos distintos, **A debe declarar B
directamente en dependencies**. Que B esté activo o sea una dependencia transitiva no sustituye esa declaración.
Se rechaza con `MODULES_DEPENDENCY_UNDECLARED` antes de publicar; no se añade la dependencia automáticamente.
La propiedad se obtiene del registro de fuentes, no del prefijo del ID, nombre de paquete ni ruta.

Los procesadores informan referencias tipadas obligatorias. El perfil comprueba bindings de lógico a físico y
diccionario, origen de proyecciones, menú al que se aporta, padre de una entrada y destino de proyección. El
procesador ilustrativo de traducciones informa propietarios de claves conocidas; las extensiones informan sus
referencias mediante evidencia privada del procesador. No se trata todo texto como referencia ni se publica una
gramática I18N o de extensiones. Si falta el destino obligatorio informado, se rechaza con `MODULES_REFERENCE_MISSING`
o el diagnóstico de referencia del consumidor existente. Los hechos de FK físicos no identifican módulos por nombre.

Una referencia al mismo módulo no añade dependencia. La aplicación puede orquestar definiciones de módulos activos;
una referencia a una definición del host es una precondición del registro, no una dependencia a un módulo ficticio
application. Las referencias deben existir igualmente. Las aportaciones originales de menú se comprueban antes de
las ediciones de la aplicación: una exclusión o sustitución no oculta una dependencia de módulo no declarada.
Una declaración incompleta tampoco permite publicar referencias ausentes en CDS o menús.

La selección de fuentes, validación de consumidores, composición de menús y plan de invalidación forman una única
publicación lógica. Ninguna etapa fallida publica un subconjunto de la nueva configuración. La generación anterior
puede seguir identificada como anterior, según las reglas existentes, pero nunca como aceptación de la nueva.
Una revocación de acceso del host se respeta aunque reconstruir falle: conservar una instantánea no concede acceso.

No hay “gana la aplicación” ni “gana el último módulo” para DICT/CDS: duplicados en el mismo espacio de tipo fallan
incluso si son idénticos. IDs de tipos distintos tienen espacios independientes, según sus contratos. Las identidades
proveedor/fuente activas tampoco pueden repetirse con distintos propietarios. La personalización explícita de menús
de MENUS-001 no introduce overlays de diccionario ni cambios de semántica de una proyección.

## 3. Desactivación sin pérdida

Desactivar retira sus fuentes del catálogo activo y la disponibilidad de derivados/servicios dependientes. **No**
borra archivos originales, especializaciones, proyecciones, traducciones, menús autorados, tablas ni datos de negocio.
El host puede mantener una observación física de una tabla todavía existente, aunque ya no haya un lógico público
del módulo. En el escenario el proveedor físico pertenece a la aplicación y sobrevive a retirar catalog y reports.
La propiedad física no se deduce de nombres; una fuente realmente retirada deja de estar disponible como activa.

Reactivar vuelve a validar con el estado actual; no recupera sin comprobar un derivado obsoleto ni reescribe una
especialización para hacerla encajar. Si una fuente propia de la aplicación depende del módulo retirado, se necesita
una composición coherente del host; no se elimina esa fuente automáticamente para permitir la desactivación.

## 4. Una caché general por aplicación

Existe **una caché lógica general de la aplicación**, con artefactos de la aplicación y todos los módulos. No una
caché autónoma por módulo ni un catálogo global compartido por aplicaciones. Puede particionarse internamente por
tipo/contexto sin cambiar su propietario ni las garantías. La identidad del artefacto incluye aplicación y ámbito
confiable relevante: catálogos independientes, locales y decisiones de acceso no pueden contaminarse entre sí.
El uso independiente de DICT/CDS sigue sin exigir un gestor de módulos, filesystem o un backend de caché concreto.

La caché registra dependencias entre instantáneas, selecciones de aportaciones y derivados. Por ejemplo:

```text
catalog.dictionary → catalog.model → catalog.public → reports.summary → menu.primary → labels.primary.es
aplicación.physical ────────┘
```

La flecha significa “un cambio del origen invalida el destino”. Al cambiar una fuente, activación o configuración,
se invalida el cierre transitivo, incluidas dependencias de otros módulos. Se conservan los artefactos demostrablemente
ajenos al cambio. No basta invalidar todos los elementos cuyo propietario tenga el mismo ID de módulo.

Debe registrarse también la dependencia de **selección/membresía**, incluida una consulta que no encontró aportaciones:
activar reports añade una entrada a un menú ya cacheado; ese menú se invalida aunque antes no dependiera de una fuente
reports. Lo mismo aplica a referencias negativas a definiciones y a retiradas. La composición propia se sigue por menú;
las decisiones de visibilidad/localización pertenecen al contexto confiable relevante, no a un usuario global.

Solo se permite retener si las dependencias completas siguen vigentes. Si no puede demostrarse su completitud, se
invalida conservadoramente el artefacto afectable. No se presenta una generación antigua como actual. La publicación
comprueba vigencia antes de aceptar un cálculo en vuelo; dependencias cambiadas impiden incorporarlo. Un artefacto
no afectado puede retenerse en la nueva publicación después de verificar sus evidencias, sin reconstruir todo.
Grafo inválido o mezcla entre aplicaciones impide aceptar el plan. El cierre es local al contexto del host;
no promete invalidación distribuida, vigilancia de archivos, TTL, formato persistente ni coordinación de procesos.
No se implementa aquí un backend de caché ni se incorpora ARP-CACHE-001.

## 5. Empaquetado y límites del candidato

Un paquete puede suministrar recursos embebidos, árboles propios u otro proveedor explícito. No se exige que su
estructura contenga `arp/`, un manifiesto en una ruta fija ni carpetas por runtime. La aplicación puede usar
convenciones como `arp/dictionary`, `arp/models`, `arp/projections`, `arp/locales`, `arp/menus` para descubrir sus
archivos y registrarlos. Son adaptadores de descubrimiento optativos, no otra autoridad semántica.
La raíz de caché general es configurable y ajena a las definiciones versionadas, aunque esté dentro de la aplicación
e ignorada por Git. No se impone filesystem a proveedores ni una ruta a los consumidores del núcleo.

Presupuestos del perfil: 256 módulos, 256 dependencias/fuentes por módulo, 1024 fuentes activas y 4096 artefactos
cacheados; cadenas de dependencias de artefactos de hasta 64. Se conservan límites/ingesta de los consumidores
DICT/CDS. Los adaptadores deben validar antes de trabajo no acotado. Una dependencia no equivale a autorización.

## 6. Evidencia para revisión

[Escenario](../../../../../fixtures/modules/v1/scenario.json), [casos de módulos](../../../../../fixtures/modules/v1/cases.json),
[transiciones](../../../../../fixtures/modules/v1/transitions.json), [verificador](../../../../../tools/check_modules_draft.py) y
[regresiones](../../../../../tests/test_modules_draft.py). catalog aporta diccionario, modelo/proyección de artículos,
traducciones y menú; reports aporta proyección derivada, traducciones y otra entrada al mismo menú.
La aplicación aporta físico ilustrativo, diccionario, menús manuales y una extensión de ejemplo.

Los resultados `{valid,issues}` son diagnósticos de composición de definiciones, no invocaciones SERVICES ni otro
formato de lectura de registros. Los códigos MODULES_* distinguen registro, dependencias, conflictos, consumidores,
referencias obligatorias no declaradas/ausentes, fuente no disponible y grafo/ámbito de caché. El único fallo de
suministro simulado usa `execution-failure`; los
demás errores de composición usan las familias CDS correspondientes. No se publican resultados parciales nuevos.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_modules_draft.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_menus_draft.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
```

El oráculo es finito y en memoria: verifica las selecciones, el resolver CDS existente y el **plan** de invalidación;
no acredita instalación, validación escalar nativa, concurrencia real, borrado/persistencia de archivos o datos.
La preservación de instantáneas de los fixtures no es una prueba de almacenamiento de una aplicación real.

## 7. Validación local de este candidato

31 vectores de módulos, 35 de menús y 17 de ciclo de vida/caché correctos, con expectativas explícitas.
**151 pruebas Python** (106 previas y 45 del candidato) y los ocho verificadores contractuales pasan. Esta evidencia es
estática/pura; no declara conformidad de los runtimes ni prueba un backend de caché real.
Los nuevos registros/menús deben adoptar la ingesta portable de CDS-READ-001; el oráculo recibe instantáneas ya
decodificadas y no sustituye sus controles de bytes, Unicode, claves únicas o presupuestos de sintaxis.
No hay formateador configurado en la raíz. Se comprueban UTF-8, LF, sangría, longitud y whitespace en los nuevos
archivos, sin reformatear contratos previos.

La revisión añade 15 regresiones respecto de las 136 anteriores. Los fixtures distinguen propiedad real de prefijos,
dependencia directa/transitiva, referencias de menús y extensiones, permisos por operación, fuentes vacías y límites
del ámbito contextual. `processorReferences` y `projectionAccess` son evidencia confiable del arnés, no propiedades
de documentos ni permisos aportados por el cliente. Cambiar las decisiones por operación invalida las vistas de
menú del contexto correspondiente en la única caché general; no invalida modelos independientes de ese contexto.