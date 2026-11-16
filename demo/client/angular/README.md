# ARP-DEMO-001 — Cliente Angular común

Cliente local y privado de demostración en `arp-contract/demo/client/angular/`.
El [inventario](INVENTORY.md) identifica las revisiones inspeccionadas y los adaptadores pendientes por repositorio.
No es una prueba de conformidad de runtime ni un protocolo nuevo de ARP.

## Qué funciona

- Selector .NET / Java / PHP con una URL independiente por instancia. La selección conserva las URLs durante la
  sesión; no guarda credenciales ni persiste ajustes del usuario en el navegador.
- Cinco temas reales de angular-ui-runtime, incluidos shell, navegación y panel: default, alternative, cyberpunk,
  vintage y high-contrast. Se usa `provideThemeRuntime`, `ThemeService` y `ThemeShellOutlet`, sin otro motor de temas.
- Exploración de diccionario/validaciones, entidades/estructuras, proyecciones, CRUD y servicios/invocaciones.
  Se pueden seleccionar los archivos originales de cada grupo, leerlos y descargarlos.
- Los assets se copian desde fixtures y definiciones del contrato durante el build, conservando sus bytes.
  No se duplican expectativas ni se convierten números exactos a números JavaScript. `expected` nunca se muestra
  como resultado obtenido. Los ejemplos de negocio siguen en los fixtures/definiciones de demo existentes.
- Compilación Angular estricta y pruebas Chromium de selección, temas, capacidades, integridad de assets y errores.

## Qué requiere backend

**No hay endpoints de navegador en los runtimes inspeccionados.** El botón de ejecución permanece deshabilitado en
los cinco grupos, incluso con una URL configurada. No se hacen peticiones a esas URLs ni se simulan validaciones,
CRUD o servicios. La aplicación es funcional como explorador y consumidor real de temas; la ejecución remota no
está disponible todavía. Esto vale para los tres runtimes y se muestra explícitamente en la interfaz.

Los 17 tipos de diccionario sí están implementados como bibliotecas nativas. Su acceso desde el navegador necesita
un anfitrión demo en cada runtime. Las otras capacidades necesitan primero implementación real. Las rutas y los
formatos de transporte no se deducen de SERVICES-002 ni del nombre del repositorio. El inventario describe las
llamadas nativas, los requisitos del anfitrión y el siguiente cambio del cliente, sin proponer una API ficticia.

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
con la indicación «working tree», por lo que no se confunde el commit con la totalidad de cambios no confirmados.

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

Actualmente no existe un backend disponible que arrancar para conectar esta UI. Ejecutar `dotnet test`, `mvn verify`
o `composer test` en los repositorios de bibliotecas ejecuta sus pruebas; **no levanta un servicio**.
Cuando exista un anfitrión real, habrá que documentar su comando de arranque, rutas y política de origen en su
repositorio y añadir aquí el adaptador con pruebas contra esa instancia. Hasta entonces no hay comando de conexión
ni ruta que la demo pueda probar legítimamente.

## Comprobaciones

```sh
./bin/run check
```

Reconstruye la aplicación y los paquetes y ejecuta Chromium a 1440×1000 y 390×844 en otra imagen fijada por digest.
Escribe resultados JSON, trazas de fallos y capturas por tema en `artifacts/browser/`.
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

1. Crear anfitriones demo mínimos de diccionario en arp-dotnet, arp-java y arp-php según el inventario.
2. Acordar su acceso de navegador y codec exacto, y probar cada adaptador del cliente contra una instancia real.
3. Implementar progresivamente recursos, CDS, CRUD e invocaciones antes de habilitar sus acciones.

No se decide el origen declarativo de CRUD, ni se añaden formularios de negocio, workflows, roles o endpoints
contractuales. La lista de capacidades es un inventario estático por revisión, no descubrimiento de una instancia.
Esta versión no presenta un editor/validador Angular como sustituto de la autoridad del servidor y no automatiza
reintentos de mutaciones ni confirmaciones de conflicto. El build no crea releases, etiquetas o publicaciones.