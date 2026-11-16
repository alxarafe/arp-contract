# ARP-DEMO-004 — Inventario de integración actualizado

Referencias inspeccionadas el 2026-11-16; son código, no instancias descubiertas automáticamente.

| Repositorio | Revisión | Capacidad integrada |
| --- | --- | --- |
| arp-dotnet | `442cd19556a3381d47e7e26b0351aa9ee567a791` | Host ASP.NET Core de diccionario, endurecido |
| arp-java | `a76f2d59feb66eb2beca6e94c00814b3512f384d` | Host JDK HTTP de diccionario |
| arp-php | `419cb8faa9f7775968e52e08688642fb416365f1` | Host nativo PHP de diccionario |
| angular-ui-runtime | `ee60123d03f095a14c4004632c214dbd822332c2` | Core y cinco temas reales APF |

Los tres hosts usan la biblioteca real y los fixtures originales. Sus identidades/protocolos son distintos y
reconocidos explícitamente. Un único cliente consume listado, descriptor y validación según capacidades anunciadas.
Las bibliotecas mantienen `contract.ref` en `4c0f4bd0337c01c15a036910b6462e6f0e674927`.
No se implementan entidades, proyecciones, CRUD ni invocaciones. Los contratos normativos no cambian.

La ejecución real y sus límites se registran en [VALIDATION.md](VALIDATION.md). Rutas y arranque:
[MULTIRUNTIME-HOSTS.md](MULTIRUNTIME-HOSTS.md). La inspección siguiente es **histórica** y no describe el acceso
HTTP actual de Java/PHP.

---

# ARP-DEMO-001 — Inventario inspeccionado

Inspección de checkouts locales el 2026-11-16. Son repositorios de código, **no instancias de servicio**.
No se han arrancado ni certificado runtimes al elaborar este inventario.

| Repositorio | Commit inspeccionado | Implementación disponible |
| --- | --- | --- |
| arp-dotnet | `d9a0acf42b36c8473b0618c80f60bc8415b8ce6a` | Biblioteca .NET 10 de diccionario |
| arp-java | `5888272f33e48d305b95ee448c8485b56d7a14cf` | Biblioteca Java 25 de diccionario |
| arp-php | `6c4b781b9bcfe10c5b450377c7b0ab06e011fb54` | Biblioteca PHP 8.5+ de diccionario |
| angular-ui-runtime | `ee60123d03f095a14c4004632c214dbd822332c2` | Motor Angular 22 y cinco temas APF |

PHP se inspeccionó en `release/arp-dict-001-v0.1.0-rc1`; los demás en `main`.
Las bibliotecas fijan `contract.ref` en `4c0f4bd0337c01c15a036910b6462e6f0e674927`.
La evidencia de sus tests corresponde a ese candidato; no certifica el contrato actual ni esta demo.

## Actualización ARP-DEMO-002

La inspección original siguiente se conserva como referencia histórica. Esta tarea añade un host HTTP de demo
separado en `arp-dotnet/demo/DictionaryHost/` y un adaptador Angular específico para .NET/diccionario. Las APIs
nativas de la biblioteca no cambian. .NET permite ahora listar elementos, ver descriptores y validar valores
**cuando se conecta una instancia de ese host**. Java/PHP y las demás capacidades conservan sus pendientes.
Los endpoints implementados, el origen CORS, arranque/parada y pruebas se detallan en [DOTNET-HOST.md](DOTNET-HOST.md)
y en `arp-dotnet/demo/README.md`. No son un nuevo contrato normativo.

## Capacidades y acceso (inspección original)

- **Diccionario y validaciones:** las tres bibliotecas implementan catálogo, resolución, validación y normalización
  de los 17 tipos escalares. Fuente: sus README, `CatalogBuilder`, `Catalog`, pruebas y `contract.ref`.
  No hay un servidor, rutas HTTP ni adaptador de navegador en los árboles fuente inspeccionados.
- **Entidades/estructuras:** ARP-RES-001 es borrador de recursos escalares; ARP-DICT-002 compuesto no está implementado
  en estas bibliotecas. No hay un catálogo de entidades ejecutable desde el navegador.
- **Proyecciones:** hay definiciones CDS y verificadores estáticos en arp-contract; no motor CDS en los runtimes.
- **CRUD:** semántica candidata y fixtures; no persistencia ni endpoints CRUD en los runtimes inspeccionados.
- **Servicios/invocaciones:** SERVICES-001/002 aporta borradores y oráculos estáticos; no dispatcher de runtime.
- **Temas:** core real `@alxarafe/ui-runtime@0.3.0-alpha.3`, y paquetes default, alternative, cyberpunk, vintage y
  high-contrast `@0.1.0-alpha.3`, privados. Se consumen sus archivos APF y exportaciones públicas; no sus fuentes.
  Los objetivos 1.0 de validación/formularios/grids no se consideran implementados.

## Adaptadores mínimos pendientes

La aplicación no supone rutas ni un protocolo HTTP de ARP. **Configurar una URL no crea un adaptador**.
Para habilitar validación remota hace falta una aplicación demo anfitriona en cada repositorio de runtime:

| Repositorio | Llamadas nativas que el anfitrión debe envolver |
| --- | --- |
| arp-dotnet | `CatalogBuilder.BuildCatalog`, `Catalog.Resolve`, `Catalog.Validate`, `ToProjection()` |
| arp-java | `CatalogBuilder.buildCatalog`, `Catalog.resolve`, `Catalog.validate`, `projection()` |
| arp-php | `CatalogBuilder::buildCatalog`, `Catalog::resolve`, `Catalog::validate`, `descriptorJson()` |

El adaptador debe cargar fuentes registradas de la demo, conservar su revisión de catálogo/contrato, enumerar
los elementos y capacidades **realmente disponibles**, aceptar valores con el codec portable y exportar resultados
exactos. Booleanos siguen siendo booleanos; números escalares son cadenas. Los números de metadatos no deben
pasar por double ni por JSON.parse del navegador si no son representables exactamente. La aplicación anfitriona
controla identidad, ámbito, autorización, límites y filtrado de diagnósticos. Debe acordar/documentar sus rutas,
verbos, entrada/salida, errores y CORS/origen antes de añadir un adaptador específico en este cliente.
No es necesario modificar la biblioteca de dominio ni el contrato normativo para crear ese anfitrión demo.

Después, en `arp-contract/demo/client/angular`, se añadirá exclusivamente la conexión a ese adaptador documentado,
con pruebas de integración contra una instancia real. Una respuesta HTTP 200 o un repositorio Git no demuestran
capacidades ni conformidad. No hay autodetección inventada de endpoints en esta versión.

Para entidades, proyecciones, CRUD e invocaciones primero se necesitan sus implementaciones y pruebas reales en
los runtimes correspondientes. CRUD gestionado exige además evidencia de concurrencia y atomicidad de persistencia;
un manejador delegado no obtiene esas garantías por el mero hecho de registrarse. Los fixtures no sustituyen eso.