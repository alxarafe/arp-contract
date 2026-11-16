# Validación de ARP-DEMO-001

Ejecutada el 2026-11-16, en `feature/arp-demo-001`, partiendo del contrato
`7190fc5e9af0fac3749ed69d6ca895b99d2edade` y del árbol de trabajo de esta tarea.
No se arrancaron backends ni se modificaron los cuatro repositorios de referencia.

| Comprobación | Resultado |
| --- | --- |
| Build APF de core y cinco temas reales | Correcto; lockfiles originales del checkout fijado |
| Instalación del consumidor | Lockfile y dependencias previas conservados al instalar seis APF |
| Compilación Angular estricta / producción | Correcta; bundle inicial 186,72 kB, estimación transferida 52,31 kB |
| Chromium escritorio y móvil | 12/12 pruebas correctas; cero reintentos |
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

El primer pase detectó una URL visual obsoleta al cambiar rápidamente de runtime en escritorio. Se corrigió
vinculando el input a la identidad de la instancia y actualizando el estado durante la edición. El pase final
completo fue 12/12. También se evita que la configuración asíncrona sobrescriba una URL editada durante su carga.

Se inspeccionaron capturas generadas de escritorio/default y móvil/cyberpunk sin desbordamientos visibles.
Eso no equivale a aprobación visual humana ni a auditoría de accesibilidad. Los diez PNG por tema/tamaño y los
resultados JSON quedan en `artifacts/browser/`, ignorados por Git. `artifacts/packages.json` registra las sumas
SHA-256 de los seis paquetes instalados y el commit de angular-ui-runtime utilizado.

**Límite de evidencia:** no hay validaciones remotas, CRUD, invocaciones, SQL ni pruebas de conformidad de runtimes.
El navegador muestra fuentes y expectativas de fixtures, sin convertirlas en resultados observados. La ausencia
de adaptadores es explícita en la UI y se detalla por repositorio en [INVENTORY.md](INVENTORY.md).
La evidencia de tests nativos de las bibliotecas, referida por sus README, no se volvió a ejecutar aquí y no se
extrapola a la demo o al contrato actual.