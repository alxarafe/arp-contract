# ARP-DEMO-002 — Diccionario .NET real desde Angular

El cliente incorpora un adaptador **específico de demostración** para el host ASP.NET Core de
`arp-dotnet/demo/DictionaryHost/`. No define ni publica el transporte normativo de ARP.

## Recorrido disponible

Seleccionar .NET, configurar la URL base de la instancia, abrir «Diccionario y validaciones» y pulsar **Conectar**.
El cliente comprueba `GET /demo/info`: exige `demoProtocol: arp-demo-dotnet/1`, `runtime: dotnet` y las capacidades
`dictionary.list`, `dictionary.describe` y `dictionary.validate`. Después obtiene el listado real. No basta con
que una URL responda HTTP 200 ni con que exista un repositorio Git.

Al seleccionar un elemento se muestra el JSON original del descriptor. El usuario elige el tipo portable
`string`, `boolean` o `null`, introduce el valor y pulsa **Validar mediante .NET**. La respuesta observada se muestra
separada de los fixtures originales de solo lectura. Los códigos, IDs, campos y contenido recibido no se traducen.
Los estados y controles propios del panel sí usan los catálogos ES/EN existentes, con español inicial y respaldo EN.

Los descriptores se leen como texto: sus metadatos numéricos pueden superar la precisión de JavaScript. Los valores
numéricos escalares se envían como cadenas, sin `Number`, parseo decimal o redondeo. Las respuestas de validación
también se conservan como texto original, con sus valores normalizados y errores reales.

## API demo consumida

| Método | Ruta relativa a la URL configurada | Uso |
| --- | --- | --- |
| GET | `/demo/info` | Identidad del protocolo demo y capacidades reales |
| GET | `/demo/dictionary/elements` | Lista `{id,type}` de elementos |
| GET | `/demo/dictionary/elements/{id}` | Descriptor JSON exacto |
| POST | `/demo/dictionary/elements/{id}/validate` | Cuerpo `{"value":...}`; validación de biblioteca |

La definición detallada, códigos HTTP, límites, fuentes originales y CORS están en `arp-dotnet/demo/README.md`.
La biblioteca carga los 17 tipos de `fixtures/dictionary/v1/catalog.json` y el elemento de metadatos grandes de
`fixtures/dictionary/v1/sources/portable-equivalent.json`: 18 elementos, sin modificar los fixtures.

Solo .NET/diccionario dispone de esta integración. Java y PHP siguen sin adaptador; entidades, proyecciones, CRUD
y servicios no se habilitan. El botón genérico junto al explorador de fixtures permanece deshabilitado y no ejecuta
esos archivos como si fueran pruebas de conformidad. El nuevo panel dispone de sus propias acciones reales.

## Arranque y parada manual

Desde el checkout de arp-dotnet que contenga la rama de esta tarea:

```sh
export ARP_CONTRACT_PATH=/absolute/path/to/arp-contract
./demo/run build
./demo/run start
```

Desde `arp-contract/demo/client/angular/`:

```sh
./bin/run build
./bin/run start
```

Abrir **http://127.0.0.1:4173** y configurar .NET como **http://127.0.0.1:5100**. Las URLs se pueden preconfigurar en
`config/instances.json`; esta tarea mantiene el valor vacío para no afirmar que una instancia esté ejecutándose.
Cambiar el puerto del host mediante `ARP_DEMO_PORT` exige usar esa URL en el cliente. Cambiar el origen Angular
exige `ARP_DEMO_ORIGIN` en el host; `localhost` y `127.0.0.1` son orígenes distintos. CORS no es autenticación.
El host publica solo en loopback. No hay credenciales, autenticación simulada, proxy ni persistencia.

Detener el frontend con `Ctrl+C`. Desde arp-dotnet, `./demo/run stop` detiene y elimina únicamente su contenedor,
verificando la etiqueta de propietario. No se eliminan imágenes ni contenedores de otros proyectos.

## Pruebas reproducibles

Desde este directorio:

```sh
ARP_DOTNET_PATH=/absolute/path/to/arp-dotnet ./bin/integration-dotnet
```

El script compila ambos lados, arranca el host, comprueba la API y ejecuta las regresiones y los tests de integración
Chromium contra la **biblioteca real**, sin mocks de backend. Usa .NET en `127.0.0.1:5100` y Angular de prueba en
`127.0.0.1:4174`, para no tocar una previsualización existente en 4173. `ARP_DEMO_CLIENT_PORT` cambia el puerto de
prueba; el CORS se ajusta exactamente a ese origen. Usa Docker host networking en Linux para que Chromium alcance
la publicación loopback real. Otras plataformas necesitan conectividad equivalente explícita.

Al terminar o fallar se detiene y elimina el host de integración. El servidor estático de prueba pertenece al
contenedor Chromium temporal. No se publica ningún puerto de navegador hacia interfaces externas. Los resultados,
capturas y trazas permanecen en `artifacts/`, ignorados por Git.

`./bin/run check` conserva la batería autónoma de la UI, sin necesitar .NET. Los tests nativos existentes se ejecutan
en arp-dotnet con `ARP_CONFORMANCE_PATH` apuntando a un checkout limpio del commit que fija su `contract.ref`.
No se cambia esa referencia ni se extrapolan sus resultados a otras capacidades o versiones del contrato.

## Límites y comportamiento ante fallos

El estado conectado significa **última petición confirmada**, no vigilancia continua del servidor. Una operación
posterior detecta una caída; no hay heartbeat ni reintento automático. También se puede desconectar expresamente.
Cambiar URL o runtime invalida el estado anterior, aborta peticiones pendientes y evita mostrar resultados de otra
instancia. Los fetch tienen un límite de espera de ocho segundos y omiten credenciales. Editar el valor elimina la
respuesta anterior para no atribuirla a la entrada nueva. Una respuesta HTTP de error conserva sus detalles
estructurados cuando pudo recibirse; un fallo de red/CORS muestra un estado de conexión no disponible.

Solo se muestran las capacidades implementadas. La garantía de exactitud se basa en las APIs de biblioteca y en
los tests reales de INT64, DECIMAL, booleanos, null y metadatos `1e127`; no implica conformidad de CRUD, servicios,
transacciones o del transporte candidato. La aprobación de una API HTTP general queda pendiente.