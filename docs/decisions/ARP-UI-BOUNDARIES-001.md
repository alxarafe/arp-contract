# ARP-UI-BOUNDARIES-001 — Arquitectura UI / ARP-Angular / Backend

**Fecha del acuerdo:** 22 de noviembre de 2026  
**Estado:** decisiones arquitectónicas acordadas; pendiente de incorporación al repositorio.  
**Naturaleza:** documento de dirección arquitectónica. **No** publica un protocolo de red, un esquema YAML/JSON, una versión de biblioteca ni una declaración de conformidad.

## 1. Objetivo

Desarrollar aplicaciones Angular en las que los recursos y formularios estándar puedan definirse declarativamente en el backend y aparecer en el frontend con CRUD completo, sin implementar un componente Angular específico para cada recurso. Cuando las necesidades no puedan resolverse de forma declarativa, la aplicación podrá crear pantallas Angular propias y reutilizar exactamente los mismos componentes visuales.

**Regla central:** todo comportamiento y componente visual genérico pertenece a `angular-ui-runtime` (UI). `arp-angular` adapta el protocolo y los metadatos de ARP a UI; no implementa una segunda biblioteca de formularios ni un segundo motor de temas.

## 2. Límites y dependencias

| Capa | Es responsable de | No es responsable de |
| --- | --- | --- |
| `@alxarafe/ui-runtime` y temas | Composición y renderizado visual autónomos: formularios, campos simples y complejos, objetos, pestañas, secciones, paneles, grupos, menús y navegación visual, controles de selección, diálogos, estados visuales, foco, errores por campo y temas. Interfaces y eventos genéricos reutilizables. | Contratos, entidades, permisos, decisiones de negocio, transporte, persistencia o conocimiento de ARP/ERBAS. |
| `@alxarafe/arp-angular` | Comunicación y negociación con backends ARP; recepción e interpretación de metadatos de recursos, operaciones y formularios; transformación a la API pública neutral de UI; gestión de la interacción funcional CRUD; serialización de cambios y operaciones; interpretación de respuestas y diagnósticos del backend. | Implementar por duplicado pestañas, paneles, campos, formularios, validación visual, temas o navegación visual. |
| `arp-php`, `arp-java`, `arp-dotnet` | Resolver definiciones y capacidades; aplicar permisos y validación definitiva; ejecutar operaciones y persistir datos, con conectores de base de datos. | Definir componentes Angular o imponer un tema visual. |
| Aplicación consumidora (`erbas-client`, otras) | Dominio, composición de la aplicación, rutas, elección de temas y pantallas específicas. Puede usar UI directamente, con ARP-Angular o con ambos. | Reescribir componentes genéricos disponibles en UI. |

La dependencia es **unidireccional**: UI no depende de ARP, ERBAS ni de un backend. ARP-Angular consume la API pública de UI; el modelo de instalación previsto es una dependencia de pares (`peerDependency`) de UI para evitar copias independientes del motor visual. Las aplicaciones pueden consumir UI sin instalar ARP-Angular. Las bibliotecas de temas son independientes y pueden ampliarse por terceros sin modificar la lógica de ARP.

La separación no obliga a que toda aplicación adopte todas las capacidades ARP; se conserva el carácter opcional y modular de la plataforma.

## 3. Formularios y pantallas: dos vías, mismos componentes

### Vía declarativa (automática)

1. La aplicación declara en su backend los datos, las operaciones y, cuando proceda, la presentación del recurso.
2. El backend expone una definición de formulario y las capacidades efectivas por un protocolo ARP común.
3. ARP-Angular recibe la definición, la interpreta y la transforma a un modelo neutral admitido por UI.
4. UI **genera visualmente el formulario**, incluidos controles, pestañas, paneles, estructuras anidadas y estados.
5. UI emite eventos y cambios; ARP-Angular construye y envía las operaciones al backend.
6. ARP-Angular interpreta las respuestas y entrega a UI valores, disponibilidad y diagnósticos; UI los representa.

Un CRUD estándar debe poder quedar disponible en la aplicación **mediante definición**, sin crear código Angular específico de la entidad. Las rutas y entradas de menú pueden apuntar al recurso; no se presupone que cada recurso deba generar una entrada de menú implícita. Se preservan las decisiones existentes sobre composición manual/modular de menús.

### Vía manual (pantallas propias)

Una aplicación Angular puede construir cualquier pantalla usando directamente las APIs públicas de UI: por ejemplo, una ficha con tres pestañas, paneles y campos, sin tener que declarar un CRUD ni conectarse a ARP. También puede insertar componentes Angular específicos en una pantalla que reutiliza los controles generales. Las rutas propias deben convivir con las vistas ARP sin restricciones artificiosas.

**El renderizado visual utilizado por ambas vías debe ser el mismo.** La diferencia radica en la procedencia de la definición y quién maneja la interacción funcional, no en duplicar los componentes.

## 4. Regla de evolución de UI

Antes de implementar una nueva necesidad visual en ARP-Angular, ERBAS u otra aplicación, comprobar si es una capacidad genérica. Si lo es, **ampliar primero UI**, definir su API pública y añadir demostración y pruebas. No crear componentes paralelos por comodidad local. La lógica específica de negocio permanece en la aplicación y no se traslada a UI.

UI debe cubrir, en su desarrollo progresivo, toda la infraestructura visual reutilizable necesaria para los formularios y pantallas previstas: composición, controles para tipos simples y objetos, validaciones y estados visibles, menús, ventanas/áreas de trabajo, paneles, temas y extensibilidad. Esto es **objetivo**, no afirmación de que todas esas capacidades estén implementadas ya.

## 5. Protocolo frontend / backend

ARP-Angular es el adaptador Angular del contrato común de ARP; debe funcionar con cualquier backend que implemente las mismas capacidades (`arp-php`, `arp-java`, `arp-dotnet`), sin introducir lógica exclusiva de PHP.

El protocolo deberá definir, cuando se aborde su contrato formal: descubrimiento de capacidades y versiones, definiciones de recursos y formularios, operaciones y cambios, tipos de valor sin pérdida, errores vinculados a campos, conflictos y respuestas. No se fija aquí su sintaxis, endpoints ni un formato de archivo obligatorio. El backend puede construir la definición a partir de YAML/CDS, pero **UI no interpreta YAML ni depende de su formato**. El protocolo HTTP de la demostración actual no se declara, por este acuerdo, contrato definitivo de ARP.

La presentación y las validaciones locales nunca sustituyen la autorización, la validación definitiva, los controles de concurrencia ni la persistencia del servidor.

## 6. Requisitos de experiencia de usuario ya acordados

- Los CRUD automáticos deben presentar los errores de campo **junto al campo afectado**, destacarlo visualmente con el tema activo y conservar los datos introducidos.
- Deben poder mostrarse **varios errores simultáneamente**; los errores no atribuibles a un campo se muestran a nivel de formulario.
- Los campos no editables se distinguen visualmente y no se envían como modificables. El foco puede dirigirse al primer campo inválido.
- Un campo generado automáticamente no debe solicitar valor al usuario en el alta ordinaria; se muestra como dato no editable cuando corresponda. La semántica de generación y de importaciones autorizadas pertenece al backend y sus conectores, no al tema visual.
- CREATE no sobrescribe un registro existente cuando hay colisión de clave. Las extensiones de generación automática, UUID, plantillas y las políticas exactas de importación se abordarán de forma separada, sin bloquear esta arquitectura.
- No se codifican excepciones específicas de campos de demostración como `code`, `id` o `rating`; las reglas son genéricas y se derivan de metadatos y respuestas del backend.

## 7. Recuperación del trabajo previo

No se deben perder las capacidades desarrolladas en `erbas-client` ni en `angular-ui-runtime`. Antes de mover código debe elaborarse un inventario exhaustivo que identifique: funcionalidad actual, responsable correcto, API pública propuesta, pruebas de regresión y diferencias respecto al contrato ARP.

Entre las capacidades existentes a preservar e integrar se encuentran: temas Default, Alternative, Cyberpunk, Vintage y High Contrast; shell, navegación y paneles; renderer de tipos semánticos; composición de `ResourceLayout` con pestañas/secciones/grupos; formularios dinámicos; relaciones y selectores; acciones; campos inmutables; presentación contextual y pantallas Angular compiladas propias. **No se presume que todas estas capacidades ya formen parte del paquete público UI**: varias siguen implementadas en `erbas-client`.

`erbas-client` debe ser consumidor de las bibliotecas compartidas, no el lugar definitivo donde mantener implementaciones visuales reutilizables. La extracción no debe eliminar sus funciones ni introducir regresiones.

## 8. Demo visual autónoma de UI

Ampliar el `apps/testbed/` existente, que debe continuar siendo autónomo, privado y no distribuido. La demo debe **mostrar visualmente todas las funcionalidades públicas implementadas de UI** y permitir comprobar cada tema, sus variantes y los cambios de tema con estado conservado.

Se exige un ejemplo verificable de formulario complejo con **tres pestañas**, paneles, secciones, campos de distintos tipos (incluidos objetos cuando exista soporte), errores simultáneos por campo, estados de solo lectura y componentes propios insertables. La demo no requiere ARP, ERBAS, servicios HTTP ni una base de datos. No debe fingir como implementadas capacidades previstas pero todavía ausentes.

Las pruebas deben comprobar tanto el resultado funcional como la composición visual, la navegación con teclado, el foco y la compatibilidad con temas. Se mantienen las condiciones de validación y empaquetado de `angular-ui-runtime`.

## 9. Orden de trabajo y criterios de cierre

1. **AUR-CAPABILITIES-001 — Inventario y preservación.** Comparar el API público de UI, el testbed y las capacidades actualmente en ERBAS; localizar duplicidades y carencias sin reescritura prematura.
2. **UI — Completar composición visual.** Extraer o implementar las piezas visuales genéricas necesarias, manteniendo UI autónomo y con contratos públicos de componentes.
3. **UI — Completar demo visual y pruebas.** Cada capacidad pública debe ser observable en el testbed, incluyendo el formulario complejo de tres pestañas.
4. **ARP-ANGULAR-001 — Biblioteca adaptadora.** Implementar el consumo del protocolo ARP y el puente hacia UI; no crear componentes visuales alternativos.
5. **Prueba de consumo independiente.** Una aplicación Angular ajena a ambos repositorios debe tener al menos un CRUD generado por metadatos y una pantalla propia que utilice directamente los mismos componentes UI; ambas deben funcionar con los temas existentes y poder aceptar temas nuevos.
6. **Integración ERBAS.** Sustituir progresivamente las implementaciones genéricas duplicadas, conservando comportamiento y pruebas.

No es necesario terminar toda la versión futura 1.0 de UI antes de comenzar ARP-Angular; sí deben completarse y verificarse primero las capacidades visuales que necesite cada tramo de integración.

## 10. Restricciones para evitar desviaciones

- No trasladar diseño visual, layout, renderers o temas al adaptador ARP-Angular.
- No hacer que UI conozca CDS, operaciones ARP, bases de datos o reglas empresariales.
- No resolver carencias de UI duplicando la implementación en una aplicación consumidora.
- No inferir permisos de metadatos de presentación.
- No convertir el explorador CRUD actual en el paquete distribuible: seguirá siendo banco de pruebas técnico.
- No reescribir desde cero los componentes existentes sin inventario y pruebas de preservación.
- No aprobar mediante este documento nuevos esquemas, rutas HTTP, contratos wire, etiquetas Git, releases ni adopción de runtimes.

## 11. Referencias existentes

- `arp-contract/docs/architecture.md` y su original archivado `docs/history/2026-11-20-pre-v1/docs/architecture.md`.
- `arp-contract/docs/features/arp-modules-001.md` y `arp-menus-001.md` (documentos históricos vinculados).
- `angular-ui-runtime/README.md`, `apps/testbed/README.md`, `docs/qa/testbed.md`, `docs/contracts/ui-runtime-v1.md`.
- `erbas-client/docs/client-runtime-001.md`, `client-runtime-002.md`, `core-fe-theme-runtime.md`, `resource-presentation-001.md`.

**Criterio rector de cualquier cambio futuro:** ¿la funcionalidad es visual y reutilizable? Si la respuesta es sí, debe vivir en UI y poder usarse por una aplicación Angular sin ARP. Si es específica del contrato y de la operación ARP, debe vivir en ARP-Angular o en el backend que corresponda.
