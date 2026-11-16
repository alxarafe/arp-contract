# ARP-DEMO-004 — Diccionario real .NET, Java y PHP desde Angular

## Cliente único y negociación

`src/remote/dictionary.ts` y su plantilla son comunes. `src/remote/protocol.ts` contiene únicamente los pares de
identidad/protocolo reconocidos y filtra capacidades conocidas; no define un contrato normativo de transporte.
No hay tres clientes, ni ramas de presentación por lenguaje.

| Selección | Identidad esperada | Protocolo reconocido | URL predeterminada del host |
| --- | --- | --- | --- |
| .NET | `dotnet` | `arp-demo-dotnet/1` | `http://127.0.0.1:5100` |
| Java | `java` | `arp-demo-java/1` | `http://127.0.0.1:5200` |
| PHP | `php` | `arp-demo-php/1` | `http://127.0.0.1:5300` |

Las URLs del cliente empiezan vacías; se configuran en sesión o en `config/instances.json` antes de compilar.
Seleccionar un runtime no consulta automáticamente su URL. Conectar exige identidad y protocolo coherentes con
la selección y una lista de capacidades formada por cadenas. Un sobre desconocido o incoherente no habilita nada.

Cada operación se autoriza en la UI solo si está anunciada: `dictionary.list` permite consultar/seleccionar el
catálogo; `dictionary.describe` consultar descriptores; `dictionary.validate` enviar valores. La validación puede
estar disponible sin descriptor si existe listado. Si falta listado no se inventan IDs ni se llaman esas rutas.
Capacidades desconocidas no habilitan funciones. Esta comprobación de UI no sustituye autorización del servidor.

| Método | Ruta relativa a la URL configurada |
| --- | --- |
| GET | `/demo/info` |
| GET | `/demo/dictionary/elements` |
| GET | `/demo/dictionary/elements/{id}` |
| POST | `/demo/dictionary/elements/{id}/validate` |

Los tres hosts actuales anuncian las tres operaciones y cargan los 18 elementos de los dos fixtures originales.
Los detalles HTTP, límites, fuentes y diagnósticos pertenecen a `demo/README.md` de cada runtime. No se infieren
otras capacidades ni se habilitan entidades, CDS, CRUD o servicios desde estos endpoints.

## Exactitud y estado

Descriptores y resultados se leen como texto y se muestran íntegros, sin traducir campos/códigos ni convertir
metadatos a JavaScript Number. PHP puede escribir un entero completo donde Java/.NET usan exponente: la UI respeta
el original y las pruebas comparan el valor con BigInt. Los escalares numéricos se envían como cadenas; booleanos,
null y cadena vacía mantienen sus tipos. El cuerpo de validación es exactamente un objeto con `value`.

Cambiar runtime, URL válida/inválida, desconectar o destruir el panel aborta peticiones y descarta el estado previo.
Un número de secuencia impide publicar respuestas tardías y evita continuar una negociación obsoleta. Se limpian
catálogo, selección, descriptor, codec, entrada y resultados. Las URLs independientes por runtime se conservan
durante la sesión. Tema e idioma no cambian el destino ni invalidan una conexión; tampoco recargan fixtures.

Los fetch omiten credenciales, rechazan redirecciones y vencen a los ocho segundos. El estado conectado significa
última petición confirmada, no heartbeat. Un error HTTP de validación conserva el texto de la respuesta recibida;
un error de red/CORS invalida la conexión. No se añaden reintentos automáticos ni operaciones de escritura.

## Arranque manual

En cada repositorio de runtime con su host integrado:

```sh
export ARP_CONTRACT_PATH=/absolute/path/to/arp-contract
export ARP_DEMO_ORIGIN=http://127.0.0.1:4173
./demo/run build
./demo/run start
# Al terminar, en ese mismo repositorio y con el mismo ARP_DEMO_CONTAINER:
./demo/run stop
```

`ARP_DEMO_PORT` permite un puerto alternativo y `ARP_DEMO_CONTAINER` un nombre propio. No se debe detener un servicio
ajeno que ocupe el puerto; elegir otro y configurar su URL en Angular. Solo se publica en 127.0.0.1.

En `arp-contract/demo/client/angular`:

```sh
./bin/run build
./bin/run start
```

Abrir 4173, seleccionar runtime, configurar su URL y pulsar Conectar. Consultar un elemento y validar un valor.
Cambiar de runtime no reinicia Angular. Los cinco temas y ES inicial/EN fallback conservan el comportamiento previo.
CORS debe coincidir exactamente con el origen del navegador: localhost y 127.0.0.1 no son equivalentes.

## Integración reproducible y aislamiento

Se requieren Bash, Git, Python 3 y Docker en Linux. Angular y los tres lenguajes se compilan en contenedores;
no se instalan dependencias en el equipo. angular-ui-runtime debe estar limpio en la revisión fijada por bin/run.

```sh
./bin/integration-multiruntime
```

Busca los repositorios hermanos; se pueden usar `ARP_DOTNET_PATH`, `ARP_JAVA_PATH`, `ARP_PHP_PATH` y
`ARP_UI_RUNTIME_PATH`. Exige referencias limpias y registra sus SHA. Exporta sus árboles mediante git archive a
un directorio temporal; los builds se ejecutan allí, sin escribir siquiera artefactos en los repositorios de origen.
Los fixtures se montan en solo lectura. Salidas, logs, revisiones, trazas y capturas quedan en `artifacts/`, ignorado.

Puertos de prueba: frontend 4174, .NET 5199, Java 5299, PHP 5399. Se cambian con `ARP_DEMO_CLIENT_PORT`,
`ARP_DOTNET_DEMO_PORT`, `ARP_JAVA_DEMO_PORT`, `ARP_PHP_DEMO_PORT`. CORS se fija al origen de prueba. Los contenedores
Chromium usan host networking para alcanzar loopback; otras plataformas requieren conectividad equivalente.

La limpieza se registra antes de los arranques, guarda los IDs exactos creados y comprueba tanto tipo de demo como
propietario temporal antes de retirarlos. No se adopta un contenedor tras un arranque fallido. Se compara el estado,
hora de inicio y contador de reinicios de los contenedores preexistentes. No hay prune, eliminación de imágenes o
volúmenes ajenos, ni terminación de procesos para liberar puertos. La limpieza necesita un daemon disponible y no
puede garantizarse ante SIGKILL o fallo de Docker; las etiquetas son propiedad cooperativa, no una barrera de seguridad.

La batería ejecuta librerías reales. Solo los tests negativos de capacidades alteran deliberadamente el sobre de
información; no acreditan ejecución del backend. Las pruebas de cancelación retrasan la entrega de respuestas
obtenidas del host real y comprueban la señal de aborto y ausencia de datos tardíos. Los tests autónomos de fixtures
siguen disponibles con `bin/run check`, sin arrancar backends.

`bin/integration-dotnet` queda como alias de integración completa; ahora requiere las tres referencias.
Esto verifica el alcance demostrado, no conformidad normativa general ni un nuevo protocolo ARP publicado.