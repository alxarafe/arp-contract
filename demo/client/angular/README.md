# ARP-DEMO-001 — Cliente Angular común

Cliente local y privado de demostración en `arp-contract/demo/client/angular/`.
El [inventario](INVENTORY.md) identifica las revisiones inspeccionadas y los adaptadores pendientes por repositorio.
No es una prueba de conformidad de runtime ni un protocolo nuevo de ARP.

## Qué funciona

- Selector .NET / Java / PHP con una URL independiente por instancia. La selección conserva las URLs durante la
  sesión; no guarda credenciales ni persiste URLs del usuario en el navegador.
- Selector Español / English, con español inicial y cambio inmediato sin recargar. Solo el idioma se conserva en
  `localStorage`; se recupera en visitas posteriores.
- Cinco temas reales de angular-ui-runtime, incluidos shell, navegación y panel: default, alternative, cyberpunk,
  vintage y high-contrast. Se usa `provideThemeRuntime`, `ThemeService` y `ThemeShellOutlet`, sin otro motor de temas.
- Exploración de diccionario/validaciones, entidades/estructuras, proyecciones, CRUD y servicios/invocaciones.
  Se pueden seleccionar los archivos originales de cada grupo, leerlos y descargarlos.
- Los assets se copian desde fixtures y definiciones del contrato durante el build, conservando sus bytes.
  No se duplican expectativas ni se convierten números exactos a números JavaScript. `expected` nunca se muestra
  como resultado obtenido. Los ejemplos de negocio siguen en los fixtures/definiciones de demo existentes.
- Compilación Angular estricta y pruebas Chromium de selección, temas, capacidades, integridad de assets y errores.

## Idiomas y traducciones

La cabecera permite seleccionar **Español (`es`) / English (`en`)** junto a Runtime y Tema. El idioma inicial es
español, independientemente del idioma del navegador. Se recupera la preferencia válida de la clave
`arp-demo.language` en `localStorage`; un valor ausente o desconocido usa español. Si el almacenamiento está bloqueado
o lleno, se puede seguir cambiando el idioma durante la sesión. No se persisten las URLs ni otros datos de trabajo.

Los catálogos independientes `src/i18n/en.ts` y `src/i18n/es.ts` centralizan todos los textos propios de la interfaz,
los mensajes de error, estados, navegación, título del documento y etiquetas accesibles. Las claves están tipadas
a partir del **catálogo de referencia completo inglés**. Para añadir textos, definir primero su clave y traducción
inglesa y después la española. Un error ya visible cambia de idioma sin perder su causa.

**Respaldo: ES → EN.** Si falta una traducción española, se utiliza la inglesa. Si falta también la inglesa, se
muestra `[i18n:clave]`. En desarrollo se emite un aviso de consola por clave ausente; en producción se conserva el
marcador sin añadir avisos. La selección inglesa no usa español como respaldo. Las pruebas inyectan catálogos
incompletos en el resolvedor para comprobar ambos casos sin retirar traducciones reales de la aplicación.

El cambio no recarga la aplicación ni los assets: conserva runtime, URLs, tema, archivo seleccionado, contenido y
borradores de entrada. También actualiza `html.lang` y el título de la pestaña. No traduce identificadores de temas,
runtimes, campos, rutas, códigos contractuales ni los bytes originales de fixtures y definiciones. No modifica los
textos internos de paquetes de terceros. Se utilizan señales y servicios de Angular, sin dependencias nuevas.

## Qué requiere backend

**.NET/diccionario dispone ahora de un host real y un adaptador de demo**, documentados en
[DOTNET-HOST.md](DOTNET-HOST.md). Permite consultar elementos/descriptores y validar valores con la biblioteca .NET
real. Configurar la URL no conecta automáticamente: es necesario pulsar Conectar y superar la comprobación de
información/capacidades del host. La UI distingue respuesta observada del host y expectativas estáticas de fixtures.

Java y PHP siguen sin endpoints ni adaptadores de navegador en los repositorios inspeccionados. Las otras
capacidades continúan pendientes en todos los runtimes. Sus acciones no se habilitan ni se simulan validaciones,
CRUD o servicios. El [inventario](INVENTORY.md) conserva la inspección inicial y registra la ampliación .NET.

## Arranque reproducible

Se requieren Bash, Git y acceso a Docker Engine; no Node.js, npm ni Angular CLI en el host.
El primer build requiere red para descargar las imágenes por digest y las dependencias por lockfile.
Los paquetes de temas son privados: no se descargan de npm ni se publican como parte de esta tarea.

Preparar un checkout **limpio** de `alxarafe/angular-ui-runtime` en el commit
`ee60123d03f095a14c4004632c214dbd822332c2`. Por defecto se busca como hermano de `arp-contract`.
Para otro directorio, definir `ARP_UI_RUNTIME_PATH` con su ruta absoluta.
La comprobación de revisión evita compilar contra una API distinta silenciosamente.

Desde este directorio:

```sh
./bin/run build
./bin/run start
```

Abrir **http://127.0.0.1:4173**. `Ctrl+C` detiene el contenedor temporal. Solo se publica el puerto en loopback.
El build copia el árbol de trabajo actual del contrato, no un catálogo remoto. La revisión de referencia se muestra
con la indicación traducida de «árbol de trabajo», por lo que no se confunde el commit con la totalidad de cambios
no confirmados.

`build` y `check` construyen el core y los cinco temas desde el checkout fijado dentro de un contenedor temporal,
con sus lockfiles originales. Instalan únicamente los archivos APF generados en una copia temporal del consumidor.
Se comprueba que el lockfile del cliente y las versiones, fuentes e integridades de sus dependencias existentes
no cambien al añadir los seis paquetes. No hay alias a fuentes TypeScript de angular-ui-runtime.
Las versiones de Angular/TypeScript siguen el consumidor del repositorio inspeccionado.

Las fuentes del contrato, el frontend y angular-ui-runtime se montan en solo lectura; únicamente
`demo/client/angular/artifacts/` recibe salida generada, paquetes y evidencia (ignorada por Git).
No se ejecutan instalaciones ni builds en los repositorios de runtime.

## Configurar instancias

Las URLs empiezan vacías, ya que no se ha confirmado ninguna instancia ejecutándose. Para preconfigurarlas,
editar `config/instances.json`, conservar las claves `dotnet`, `java`, `php` y volver a construir. También pueden
introducirse durante la sesión. Solo se admiten URLs absolutas http(s) sin credenciales; indicar una URL nunca
habilita una capacidad ni afirma que esté conectada. No introducir secretos en la configuración.

El host .NET se arranca con `arp-dotnet/demo/run build` y `arp-dotnet/demo/run start`, con el contrato montado en
solo lectura; se detiene con `arp-dotnet/demo/run stop`. Por defecto la URL es `http://127.0.0.1:5100` y CORS autoriza
solo `http://127.0.0.1:4173`. Los detalles están en [DOTNET-HOST.md](DOTNET-HOST.md).
Ejecutar `dotnet test`, `mvn verify`
o `composer test` en los repositorios de bibliotecas ejecuta sus pruebas; **no levanta un servicio**.
Para Java/PHP siguen pendientes anfitriones equivalentes; no se inventan rutas para conectarlos.

## Comprobaciones

```sh
./bin/run check
```

Reconstruye la aplicación y los paquetes, compila/ejecuta las pruebas unitarias del resolvedor de traducciones con
TypeScript y `node:test`, y ejecuta Chromium a 1440×1000 y 390×844 en otra imagen fijada por digest.
Escribe resultados JSON, trazas de fallos y capturas por tema e idioma en `artifacts/browser/`.
Las capturas ayudan a revisar el diseño; no sustituyen revisión humana ni pruebas de accesibilidad exhaustivas.
Los checks de paquetes ejecutados al construirlos pertenecen a angular-ui-runtime; tampoco certifican ARP.

Desde la raíz de arp-contract, las comprobaciones contractuales siguen siendo independientes de Angular:

```sh
python3 -m unittest discover -s tests
python3 tools/check_contract.py
python3 tools/check_cds_draft.py
python3 tools/check_cds_compatibility_draft.py
python3 tools/check_services_draft.py
python3 tools/check_service_invocation_draft.py
git diff --check
```

Ninguno de esos comandos necesita instalar el frontend. No se cambian los contratos normativos ni las bibliotecas.

## Próximos pasos y límites

1. Revisar el host/adaptador de demo .NET y crear anfitriones de diccionario en arp-java y arp-php.
2. Acordar el transporte general y ampliar pruebas reales por runtime, sin convertir la API demo en normativa.
3. Implementar progresivamente recursos, CDS, CRUD e invocaciones antes de habilitar sus acciones.

No se decide el origen declarativo de CRUD, ni se añaden formularios de negocio, workflows, roles o endpoints
contractuales. La lista de capacidades es un inventario estático por revisión, no descubrimiento de una instancia.
Esta versión no presenta un editor/validador Angular como sustituto de la autoridad del servidor y no automatiza
reintentos de mutaciones ni confirmaciones de conflicto. El build no crea releases, etiquetas o publicaciones.