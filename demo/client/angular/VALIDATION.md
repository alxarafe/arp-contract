# Validación de ARP-DEMO-001

Ejecutada el 2026-11-16, en `feature/arp-demo-001`, partiendo del contrato
`74c8f78e9ed4406d2a0638fc95dc4459b483714e` y del árbol de trabajo de internacionalización de esta tarea.
No se arrancaron backends ni se modificaron los cuatro repositorios de referencia.

| Comprobación | Resultado |
| --- | --- |
| Build APF de core y cinco temas reales | Correcto; lockfiles originales del checkout fijado |
| Instalación del consumidor | Lockfile y dependencias previas conservados al instalar seis APF |
| Compilación Angular estricta / producción | Correcta; bundle inicial 193,79 kB, estimación transferida 53,89 kB |
| Resolvedor de traducciones (`node:test`) | 4/4 pruebas unitarias correctas |
| Chromium escritorio y móvil | 24/24 pruebas correctas; cero reintentos |
| `python3 -m unittest discover -s tests` | 82/82 pruebas contractuales correctas |
| `tools/check_contract.py` | Correcto; 327 aserciones compartidas inventariadas, no pases nativos |
| `tools/check_cds_draft.py` | Correcto; 10 escenarios estáticos |
| `tools/check_cds_compatibility_draft.py` | Correcto; 17 estructurales, 10 servidor, 7 cliente, 3 altas, 4 auditoría |
| `tools/check_services_draft.py` | Correcto; 25 escenarios estáticos |
| `tools/check_service_invocation_draft.py` | Correcto; 51 escenarios estáticos |
| `git diff --check` | Sin incidencias |

Las pruebas de navegador verifican selección y separación de URLs por runtime sin llamadas a APIs inventadas,
activación de los cinco temas mediante los componentes públicos reales, las cinco categorías en cada runtime,
acciones remotas deshabilitadas, integridad byte a byte de assets representativos, errores de carga y rechazo de
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
el pase final completo incluye las cuatro pruebas unitarias, build y 24 pruebas de navegador. No hay dependencias
ni cambios de lockfile nuevos. Se conservan las correcciones anteriores de URLs y configuración asíncrona.

Se generan veinte capturas por tema, idioma y tamaño; se inspeccionó la captura móvil/default en inglés sin
desbordamientos visibles en los tres selectores.
Eso no equivale a aprobación visual humana ni a auditoría de accesibilidad. Los PNG y los
resultados JSON quedan en `artifacts/browser/`, ignorados por Git. `artifacts/packages.json` registra las sumas
SHA-256 de los seis paquetes instalados y el commit de angular-ui-runtime utilizado.

**Límite de evidencia:** no hay validaciones remotas, CRUD, invocaciones, SQL ni pruebas de conformidad de runtimes.
El navegador muestra fuentes y expectativas de fixtures, sin convertirlas en resultados observados. La ausencia
de adaptadores es explícita en la UI y se detalla por repositorio en [INVENTORY.md](INVENTORY.md).
La evidencia de tests nativos de las bibliotecas, referida por sus README, no se volvió a ejecutar aquí y no se
extrapola a la demo o al contrato actual.