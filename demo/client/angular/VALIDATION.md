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