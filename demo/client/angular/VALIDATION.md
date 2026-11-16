# Validación de ARP-DEMO-004

Ejecutada el 2026-11-16 en `feature/arp-demo-004-multiruntime`, desde `arp-contract/main`
`85c94e4a26dd1cdd1f97e0498e0b21b6afd441fb`. Solo cambia la demo Angular, sus pruebas y documentación.
Las secciones posteriores conservan resultados históricos; la tabla siguiente es la evidencia de esta tarea.

| Comprobación | Resultado |
| --- | --- |
| Core y cinco temas APF reales, instalación y Angular estricto | Correctos, sin cambios en dependencias/lockfiles |
| Unitarias de traducción | 4/4; ES inicial, respaldo EN y referencia ausente |
| Unitarias de negociación | 6/6; tres identidades, protocolos y capacidades conocidas/parciales/incorrectas |
| Chromium completo con los tres hosts reales | **74/74**, sin reintentos; escritorio 1440×1000 y móvil 390×844 |
| HTTP de cada host antes del navegador | Correcto; 18 elementos, 17 tipos, exactitud, Unicode/JSON, límites y CORS |
| Contenedores preexistentes al terminar integración | Estado, hora de arranque y reinicios sin cambios |
| Arranque con 5100 ocupado | Fallo esperado, limpieza propia y propietario del puerto intacto |
| Pruebas del contrato | **82/82**, independientes de Angular |
| Cinco verificadores contractuales existentes | Correctos; su evidencia es estática, no conformidad de runtimes |

## Comprobación de cierre

Se repitieron `bin/integration-multiruntime`, las 82 pruebas contractuales y los cinco verificadores antes del
commit: todos correctos, incluyendo 74 Chromium sin reintentos y las 10 unitarias. Se revisaron visualmente las
capturas de escritorio con Java/default/ES y móvil con cyberpunk/EN, sin problemas observados de disposición o
legibilidad en esas vistas. Esta revisión no sustituye una auditoría exhaustiva de accesibilidad.

Se comprobó el índice: solo rutas de la demo Angular, sin artefactos, dependencias instaladas ni temporales.
Paquetes/lockfiles, contratos, fixtures y repositorios de referencia permanecen intactos. El único ajuste de cierre
es una corrección de sangría en el archivo de pruebas, sin cambio de comportamiento. Formato, sintaxis y diff
comprobados de nuevo. La evidencia generada permanece ignorada por Git.

## Cobertura real y casos negativos

Chromium conecta, consulta los 18 elementos y sus descriptores, valida valores válidos/incorrectos y desconecta
contra .NET, Java y PHP. Cada runtime se prueba en ambas ventanas, los cinco temas y ES/EN. Se verifican INT64
máximo y DECIMAL grande sin redondeo, booleanos, null, cadena vacía, códigos y omisión de normalizedValue al rechazar.
El texto del descriptor y de resultados se compara directamente con el cuerpo HTTP original. Metadatos `1e127`
se comparan con BigInt: PHP puede usar notación entera completa sin ser distinto en valor.

Se realizan seis cambios sucesivos entre runtimes en cada ventana; no quedan selección, entradas ni resultados
anteriores. Un host real con identidad incorrecta no habilita operaciones, incluso con URL igual al cambiar runtime.
Los errores de conexión son reales, no respuestas inventadas.

Las pruebas de capacidades parciales modifican deliberadamente solo el sobre de información obtenido del host:
son tests negativos del consumidor, no evidencia de conformidad del backend. Comprueban que no se llama a listado
o descriptor no anunciado y que no se habilita validación ausente. Las pruebas de cancelación ejecutan el host real,
retienen su respuesta en información/listado/descriptor/validación y cambian runtime o URL: comprueban la señal de
aborto y que una respuesta tardía no repuebla el estado. No hay backend simulado en las pruebas de ejecución.

La batería incluye las 24 regresiones autónomas previas: fixtures byte a byte, navegación, idiomas, persistencia,
almacenamiento bloqueado, errores, temas y URLs. Los resultados no certifican un transporte normativo, CRUD,
servicios, persistencia ni autorización de producción.

## Entorno y reproducción

Referencias: .NET `442cd19556a3381d47e7e26b0351aa9ee567a791`, Java
`a76f2d59feb66eb2beca6e94c00814b3512f384d`, PHP `419cb8faa9f7775968e52e08688642fb416365f1` y
angular-ui-runtime `ee60123d03f095a14c4004632c214dbd822332c2`. Los hosts se construyeron desde git archive en
copias temporales; sus repositorios permanecen limpios. Fuentes originales del contrato montadas en solo lectura.

`bin/integration-multiruntime` registra revisiones y logs bajo `artifacts/multiruntime/`, y resultados JSON,
trazas/capturas bajo `artifacts/browser/`. Las imágenes Node y Chromium están fijadas por digest. Se usaron frontend
4174 y hosts 5199/5299/5399 en loopback, sin intervenir los servicios preexistentes en 4173/5100.

Instrucciones y variables en [MULTIRUNTIME-HOSTS.md](MULTIRUNTIME-HOSTS.md). La ejecución automatizada usa Docker
host networking de Linux; otras plataformas requieren conectividad equivalente. La limpieza depende de Docker
operativo y no se garantiza ante SIGKILL/caída del daemon. CORS no es autenticación; la conexión representa la última
petición confirmada, no un heartbeat. No se añaden reintentos automáticos ni se amplía el alcance contractual.

---

# Validación de ARP-DEMO-001

Ejecutada el 2026-11-16, en `feature/arp-demo-001`, partiendo del contrato
las revisiones inspeccionadas en [INVENTORY.md](INVENTORY.md) y del árbol de trabajo de ARP-DEMO-002.
El host .NET se prueba con su biblioteca real y las definiciones originales del contrato actual.
Se arrancó el nuevo host .NET en Docker para pruebas reales; Java, PHP y angular-ui-runtime permanecieron sin
modificar. La biblioteca .NET no cambia: el host está separado bajo `arp-dotnet/demo/`.

| Comprobación | Resultado |
| --- | --- |
| Build APF de core y cinco temas reales | Correcto; lockfiles originales del checkout fijado |
| Instalación del consumidor | Lockfile y dependencias previas conservados al instalar seis APF |
| Compilación Angular estricta / producción | Correcta; bundle inicial aprox. 205 kB, estimación transferida 56,4 kB |
| Resolvedor de traducciones (`node:test`) | 4/4 pruebas unitarias correctas |
| Chromium autónomo sin backend | 24/24 pruebas correctas; cero reintentos |
| Chromium con host .NET real | 32/32 pruebas correctas; escritorio/móvil, ES/EN y cinco temas |
| .NET solución existente | 362/362 pruebas correctas contra su commit contractual fijado |
| API .NET real | 18 elementos, 17 vectores originales, validación exacta, errores, límites y CORS |
| Formato C# del host | `dotnet format whitespace --verify-no-changes` correcto |
| `python3 -m unittest discover -s tests` | 82/82 pruebas contractuales correctas |
| `tools/check_contract.py` | Correcto; 327 aserciones compartidas inventariadas, no pases nativos |
| `tools/check_cds_draft.py` | Correcto; 10 escenarios estáticos |
| `tools/check_cds_compatibility_draft.py` | Correcto; 17 estructurales, 10 servidor, 7 cliente, 3 altas, 4 auditoría |
| `tools/check_services_draft.py` | Correcto; 25 escenarios estáticos |
| `tools/check_service_invocation_draft.py` | Correcto; 51 escenarios estáticos |
| `git diff --check` | Sin incidencias |

Las pruebas de navegador verifican selección y separación de URLs por runtime sin llamadas a APIs inventadas,
activación de los cinco temas mediante los componentes públicos reales, las cinco categorías en cada runtime,
capacidades pendientes deshabilitadas, integridad byte a byte de assets representativos, errores de carga y rechazo de
URLs con credenciales o esquemas distintos de http(s).

La ampliación ES/EN añade pruebas de español inicial, cambio inmediato sin recarga, persistencia y recuperación
con `localStorage`, valores almacenados desconocidos y almacenamiento bloqueado. Comprueba la conservación de
runtime, URLs por instancia, tema, archivo, bytes del fixture y borrador de entrada al cambiar idioma; no se
vuelven a consultar los assets. Los errores ya visibles cambian de idioma, al igual que la navegación, título
y `html.lang`. Los cinco temas reales se prueban en ambos idiomas y tamaños.

Las cuatro pruebas unitarias compilan el mismo resolvedor utilizado por la aplicación. Comprueban la cobertura
del catálogo inglés de referencia, respaldo ES → EN ante una traducción española ausente, marcador
`[i18n:heading.title]` y llamada al hook de diagnóstico cuando faltan ambas traducciones, y ausencia de respaldo
inverso EN → ES. Los catálogos incompletos se inyectan solo en pruebas; ambos catálogos de aplicación conservan
todas las traducciones actuales. El servicio limita los avisos de desarrollo a uno por clave y no avisa en producción.

El primer intento de compilar las pruebas unitarias requirió declarar `rootDir` explícitamente para TypeScript 6;
el pase de ARP-DEMO-001 incluyó las cuatro pruebas unitarias, build y 24 pruebas de navegador. No hay dependencias
ni cambios de lockfile nuevos. Se conservan las correcciones anteriores de URLs y configuración asíncrona.

Se generan veinte capturas por tema, idioma y tamaño; se inspeccionó la captura móvil/default en inglés sin
desbordamientos visibles en los tres selectores.
Eso no equivale a aprobación visual humana ni a auditoría de accesibilidad. Los PNG y los
resultados JSON quedan en `artifacts/browser/`, ignorados por Git. `artifacts/packages.json` registra las sumas
SHA-256 de los seis paquetes instalados y el commit de angular-ui-runtime utilizado.

## Evidencia específica ARP-DEMO-002

`ARP_DOTNET_PATH=/ruta/al/checkout/arp-dotnet ./bin/integration-dotnet` reconstruyó ambos lados y ejecutó peticiones
cross-origin desde Chromium contra ASP.NET/.NET real, sin mocks de backend. Angular usa 4174 en estas pruebas;
5100 publica el host exclusivamente en loopback. El CORS se configura a ese origen exacto. El servidor ajeno que
ya ocupaba 4173 no se detuvo ni se reutilizó. Las pruebas no habilitan capacidades por tener una URL configurada.

La revisión visual del panel en móvil confirmó su legibilidad y detectó una selección inicial de tema que podía
mostrar `alternative` mientras el motor usaba `default`. Se vinculó expresamente la selección de las opciones al
motor real y se añadió una aserción de regresión; no se duplica la lógica de activación.

La UI comprobó listado real de 18 elementos, descriptores numéricos exactos, INT64 máximo, DECIMAL grande sin
redondeo, valores válidos/inválidos, booleanos, null y cadenas vacías; separación de resultados/fixtures, descarte
de respuesta al editar, desconexión expresa, invalidación por URL/runtime y error ante conexión rechazada real.
La validación continuó funcionando tras cambiar entre los cinco temas y ambos idiomas.

El host se compiló por separado con restore bloqueado y sin añadir paquetes a la biblioteca. La solución existente
pasó 362 pruebas contra un checkout limpio del commit `4c0f4bd0337c01c15a036910b6462e6f0e674927`, sin cambiar su
`contract.ref`. Los checks HTTP reutilizan los 17 vectores originales por tipo y verifican los hashes de fuentes,
`1e127`, tipos JSON, rechazo de datos inválidos, errores 400/403/404/405/413/415 y preflight CORS. La compilación
incluye el verificador de formato .NET limitado al nuevo Program.cs. Los contenedores de host de prueba se detienen
y eliminan automáticamente, también si falla la prueba; no se eliminan contenedores ajenos.

**Límite de evidencia:** solo diccionario .NET dispone de consulta/validación remota. No se prueba SQL, entidades,
CRUD, proyecciones ejecutables, servicios o autorización de producción. La API HTTP es solo de demostración,
pendiente de aprobación como transporte general. El estado es «última petición confirmada», no heartbeat.
La evidencia nativa corresponde al candidato fijado por la biblioteca, no a conformidad global con cada capacidad
del contrato actual. La compatibilidad Docker host-network de integración está comprobada en Linux.