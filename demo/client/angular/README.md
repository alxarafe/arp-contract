# ARP-DEMO-004 — Cliente Angular común para tres runtimes

Cliente local y privado de demostración en `arp-contract/demo/client/angular/`.
El [inventario](INVENTORY.md) identifica las revisiones inspeccionadas y los adaptadores pendientes por repositorio.
No es una prueba de conformidad de runtime ni un protocolo nuevo de ARP.

## CRUD PHP/MariaDB

El CRUD real desde el navegador, su arranque y sus pruebas se documentan en [CRUD-PHP.md](CRUD-PHP.md).

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

Los hosts de diccionario .NET, Java y PHP se consumen mediante **un único componente y negociación común**.
Configurar una URL no conecta automáticamente: pulsar Conectar verifica identidad, protocolo reconocido y
capacidades anunciadas antes de habilitar operaciones. La UI conserva las respuestas originales, separadas de
las expectativas estáticas. El CRUD PHP/MariaDB se integra mediante su panel propio; las demás capacidades conservan sus pendientes.

El listado, descriptor y validación se habilitan según `dictionary.list`, `dictionary.describe` y
`dictionary.validate`. Un host sin alguna capacidad no la adquiere por pertenecer a un runtime reconocido.
Los detalles del protocolo de demo, arranque, pruebas y límites están en [MULTIRUNTIME-HOSTS.md](MULTIRUNTIME-HOSTS.md).

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

En cada repositorio de runtime, `./demo/run build`, `./demo/run start` y `./demo/run stop` construyen, arrancan y
detienen su propio host. Puertos predeterminados: .NET 5100, Java 5200 y PHP 5300, siempre en 127.0.0.1.
Usar `ARP_CONTRACT_PATH` para el contrato y `ARP_DEMO_ORIGIN` para el origen Angular exacto; por defecto 4173.
`ARP_DEMO_PORT` y `ARP_DEMO_CONTAINER` permiten puertos/nombres alternativos. Las instrucciones completas figuran en
[MULTIRUNTIME-HOSTS.md](MULTIRUNTIME-HOSTS.md) y en `demo/README.md` de cada runtime.
Ejecutar tests de una biblioteca no levanta un servicio. Tampoco se descubre una instancia desde su repositorio Git.

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

Para integración real de los tres hosts, desde este directorio:

```sh
./bin/integration-multiruntime
```

Usa copias temporales de revisiones limpias de los runtimes, preservando sus repositorios. Prueba Chromium en
escritorio/móvil, ES/EN, cinco temas, cambios sucesivos, abortos y resultados reales. Los casos de negociación
incompleta modifican deliberadamente el sobre de información; no se usan como prueba de capacidades del backend.
`bin/integration-dotnet` queda como alias de la batería completa, que ahora necesita los tres hosts.

## Próximos pasos y límites

1. Revisar la integración común y mantener sus pruebas contra las revisiones reconocidas de los tres hosts.
2. Acordar el transporte general y ampliar pruebas reales por runtime, sin convertir la API demo en normativa.
3. Implementar progresivamente recursos, otras proyecciones e invocaciones antes de habilitar sus acciones.

No se decide el origen declarativo de CRUD, ni se añaden formularios de negocio, workflows, roles o endpoints
contractuales. Las tarjetas de capacidades son un inventario; el panel de diccionario negocia las operaciones
de la instancia.
La negociación de demo no acredita conformidad normativa ni descubre capacidades de otros módulos.
Esta versión no presenta un editor/validador Angular como sustituto de la autoridad del servidor y no automatiza
reintentos de mutaciones ni confirmaciones de conflicto. El build no crea releases, etiquetas o publicaciones.