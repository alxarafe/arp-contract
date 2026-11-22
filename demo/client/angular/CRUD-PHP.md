# ARP-DEMO-CRUD-001B — Angular y PHP/MariaDB

Integración local del cliente existente con el protocolo de demostración `arp-demo-php-crud/1`.
No modifica contratos normativos, el núcleo PHP ni `angular-ui-runtime`; no publica un nuevo protocolo ARP.

## Uso desde el navegador

1. Preparar un checkout de `arp-php` que incluya la PR #18 fusionada. Seguir su `demo/CRUD.md` y arrancar
   `python3 demo/crud-run start`, con `ARP_WRITE_CONTRACT_PATH` apuntando a un checkout limpio del commit de
   `write-contract.ref`. El host prepara los 30 registros CSV en su propio MariaDB.
2. Configurar el origen permitido del PHP como `http://127.0.0.1:4173`, o el origen exacto elegido para Angular.
   Mantener los servicios exclusivamente en loopback; no usar esta demostración como servicio de producción.
3. En este repositorio, ejecutar `demo/client/angular/bin/run build` y `demo/client/angular/bin/run start`.
   Usar `ARP_UI_RUNTIME_PATH` si el checkout limpio de `angular-ui-runtime` no está en el directorio hermano.
   Se reutilizan los seis paquetes públicos de la revisión ya fijada `ee60123d03f095a14c4004632c214dbd822332c2`.
4. Abrir `http://127.0.0.1:4173`, seleccionar PHP y escribir la URL de su instancia (por defecto
   `http://127.0.0.1:5300`). Seleccionar la tarjeta CRUD.
5. Introducir en el campo de contraseña el token de la propiedad `token` del archivo privado que imprime
   el arrancador PHP. **No copiar la propiedad `password`**: es la credencial de MariaDB y permanece en el servidor.
6. Pulsar Conectar. El cliente consulta `/demo/info` sin credenciales, verifica identidad PHP y las capacidades
   `crud.metadata` y `crud.invoke`, y solo entonces solicita `/demo/crud/metadata` con Bearer.
   Sin capacidades o con otra identidad no envía el token ni habilita operaciones.
7. Usar Consultar para GET, Crear registro, Modificar o Eliminar. El listado carga diez filas por defecto;
   Anterior y Siguiente recorren los 30 registros iniciales según los límites anunciados por el servidor.
8. Desconectar y ejecutar `python3 demo/crud-run stop` en el checkout PHP al terminar. El servidor estático
   Angular se detiene con Ctrl+C.

El panel se habilita a partir de los metadatos y muestra únicamente las operaciones anunciadas. Los nombres,
tipos, orden, etiquetas, restricciones, nulabilidad y claves de los campos proceden de esos metadatos;
el componente no contiene nombres de campos ni del target de negocio. Se admiten valores escalares simples,
con entrada textual exacta y booleanos/null de sus propios tipos JSON. La validación definitiva y las reglas
de negocio corresponden al núcleo del servidor. Las claves se introducen al crear y son de solo lectura al editar.
No se añaden relaciones, multibase, formularios complejos ni selección de conexiones o archivos.

## Sesión, idiomas y temas

El token se conserva exclusivamente en memoria del componente y se retira del campo tras Conectar. No se
escribe en localStorage, sessionStorage, cookies, URL ni configuración. Desconectar, cambiar URL/runtime,
salir del panel o recargar la página lo elimina. Un 403 durante una operación también elimina la sesión.
Las peticiones usan `credentials: omit`, rechazan redirecciones y se cancelan al invalidar la sesión.
El host exige su token y su política de origen: CORS no se usa como autenticación.

Español e inglés cubren todas las acciones y estados nuevos. Las etiquetas de negocio recibidas del backend,
identificadores, restricciones y diagnósticos originales se mantienen sin traducción. El cambio de idioma y
los cinco temas conservan los borradores y la sesión mediante las vistas retenidas de `ThemeShellOutlet`.
Los fixtures, su descarga y el diccionario en vivo conservan su comportamiento anterior. El botón de ejecución
del explorador estático sigue desactivado: las acciones reales están en el panel CRUD, separado de los fixtures.

INTEGER y DECIMAL viajan como cadenas, sin `Number`, `parseFloat`, campos HTML `number` ni cálculos de coma flotante.
El lector JSON conserva el texto fuente de números de metadatos que no son enteros seguros. Requiere un navegador
con soporte de `JSON.parse` reviver context; si falta, falla explícitamente al recibir números y no redondea.
Se verifica con Chromium. La tabla demo tiene INTEGER de 32 bits y rating acotado; las pruebas de valores más
largos y fracciones de metadatos se realizan sobre el decodificador, sin ampliar el esquema MariaDB de la demo.

## Concurrencia y diagnósticos

- UPDATE envía solo los campos modificados y el baseline del GET mostrado. Las claves y campos intactos no se
  envían como cambios. Un conflicto muestra el cuerpo original y bloquea Guardar. Recargar registro hace otro GET,
  descarta el borrador y exige volver a decidir; no existe opción de sobrescribir ni confirmación persistente.
- Eliminar realiza un GET y muestra todos los valores antes de pedir consentimiento mediante una casilla explícita.
  Cancelar no escribe. La confirmación envía exactamente la clave y los `confirmedValues` mostrados. No se hace
  otro GET al confirmar ni se reemplaza el estado consentido por una lectura más reciente. El host compone su
  `readForDelete()` y DELETE en una sola instancia y rechaza los cambios concurrentes. El cliente nunca recibe
  ni fabrica evidencia privada del núcleo.
- Un conflicto DELETE bloquea el botón. Recargar vuelve a la consulta; hay que abrir de nuevo Eliminar y confirmar
  los valores actuales. La casilla nunca se reutiliza como consentimiento de otro estado.
- Los cuerpos de rechazo y sus diagnósticos se muestran como texto JSON original. Un error de red después de una
  escritura puede tener resultado incierto: se bloquea el reintento del formulario. Consultar o actualizar el listado
  antes de decidir de nuevo; cancelar una petición no garantiza deshacer una escritura ya recibida por el servidor.
- La paginación es la adaptación acotada del host PHP: no es un snapshot entre peticiones y altas/bajas concurrentes
  pueden desplazar páginas. Las comprobaciones comparan estado, no historial: A→B→A no se distingue de A.

## Prueba reproducible Angular–HTTP–MariaDB

Requisitos: Linux con Docker, Git, Python 3.12 o posterior y los dos checkouts de referencia limpios.
No se necesita Node, PHP ni MariaDB instalados en el equipo. La construcción puede descargar imágenes y dependencias.

```sh
export ARP_UI_RUNTIME_PATH=/ruta/angular-ui-runtime
export ARP_PHP_PATH=/ruta/arp-php
python3 demo/client/angular/bin/integration-crud
```

El procedimiento:

- Construye el cliente con Angular estricto y ejecuta las pruebas unitarias, consumiendo los paquetes públicos
  existentes sin modificar `angular-ui-runtime`.
- Exporta el commit PHP a un directorio temporal propio y crea un checkout separado del contrato fijado por PHP.
  Arranca su `crud-run` con MariaDB nuevo y 30 registros CSV, sin usar bases ni contenedores existentes.
- Publica HTTP únicamente en `127.0.0.1:5398`. El servidor Angular de pruebas escucha en `127.0.0.1:4175`.
  `ARP_DEMO_PORT` y `ARP_DEMO_CLIENT_PORT` permiten elegir otros puertos libres. No publica el puerto de MariaDB.
- Ejecuta Playwright Chromium en escritorio (1440×1000) y móvil (390×844), con ambos idiomas: recorre las tres
  páginas, consulta Unicode, crea, verifica persistencia, modifica parcialmente sin alterar otros campos,
  provoca conflictos UPDATE y DELETE con otro cliente HTTP, recarga y elimina mediante consentimiento renovado.
- Comprueba rechazos de validación, token inválido, negociación incompatible, borrado de credenciales en memoria
  al cambiar runtime y ausencia del token en los almacenes del navegador. Las pruebas unitarias también comprueban
  nombres de campos arbitrarios, capacidades parciales y precisión fuera del rango seguro de JavaScript.
- Ejecuta las pruebas de navegador anteriores del explorador, idiomas y los cinco temas. El CRUD se prueba en cada
  tema conservando la sesión y el formulario. No utiliza respuestas CRUD simuladas ni una base en memoria.
- Compara por HTTP todos los registros finales con los 30 originales, no solo su cantidad. Las altas temporales
  usan claves fuera del CSV y se retiran en `finally`. La limpieza del arrancador PHP se ejecuta también si falla
  una prueba: elimina solo contenedores/volúmenes y red propios por ID y etiqueta de propiedad.

Los resultados quedan en `artifacts/browser/results.json`, capturas de los temas y `artifacts/crud-integration.json`
(ignorados por Git). Las pruebas CRUD desactivan trazas, vídeo y capturas automáticas de fallos para evitar
registrar el campo del token; sus capturas explícitas se toman ya conectado, sin el campo de credenciales.
El informe de integración registra el commit PHP, el pin de contrato y la conservación de las 30 filas.

`bin/run check` sigue ejecutando la batería de UI sin un backend. Las pruebas CRUD se habilitan solo en la
integración real; las pruebas multiruntime conservan su procedimiento independiente `bin/integration-multiruntime`.
