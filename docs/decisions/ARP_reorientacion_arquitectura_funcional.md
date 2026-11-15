# ARP — Recuperación del objetivo y arquitectura funcional

**Fecha:** 15 de noviembre de 2026
**Estado:** Documento de análisis y propuesta; pendiente de contraste con la especificación original y el código existente.

## Diagnóstico

Hemos empezado a confundir la construcción de ARP con la construcción de aplicaciones sobre ARP. Esta confusión puede llevarnos a desarrollar componentes técnicamente correctos, pero que no responden al objetivo original.

> **ARP es una plataforma autónoma, declarativa, agnóstica y modular para acelerar el desarrollo de aplicaciones empresariales.**
>
> Proporciona herramientas, contratos, metadatos, servicios y mecanismos de ejecución reutilizables, sin imponer un ERP, un lenguaje, un framework o una tecnología de persistencia concreta.

ARP no debe saber qué es un artículo, un almacén, una factura o un pedido. Debe proporcionar los mecanismos para que Erbas, Solúcar o cualquier otra aplicación puedan definir esos conceptos y desarrollar su comportamiento con el mínimo código posible.

**ARP no tiene que incorporar las reglas de negocio de las aplicaciones, pero sí debe proporcionar mecanismos para definirlas, validarlas y ejecutarlas.**

## 1. Qué queremos construir realmente

El referente principal no es SAP ERP, S/4HANA ni sus módulos funcionales, sino las capacidades de desarrollo de SAP:

- **ABAP Dictionary:** sistema de tipos y definiciones.
- **CDS:** lenguaje declarativo para modelos, relaciones, consultas y proyecciones.
- **RAP:** modelo para definir comportamientos, operaciones y servicios.
- **CAP:** entorno para construir aplicaciones y servicios a partir de modelos declarativos.
- **SAP Build:** capacidades de reglas, decisiones y automatización.
- **Integration Suite (futuro):** capacidades de integración entre sistemas.

CAP permite definir modelos semánticos y servicios que después aprovechan implementaciones genéricas para operaciones habituales. RAP permite declarar comportamientos y utilizar implementaciones gestionadas o específicas.

El objetivo de ARP no es reproducir SAP, sino **aprovechar esos principios para construir una plataforma mucho más pequeña, independiente y reutilizable**.

## 2. Arquitectura funcional que debería tener ARP

| Capacidad | Referente SAP | Responsabilidad de ARP |
|---|---|---|
| **Diccionario** | ABAP Dictionary | Tipos, dominios, campos, estructuras, restricciones y referencias. |
| **Modelo semántico** | CDS | Entidades, asociaciones, expresiones, consultas y proyecciones. |
| **Comportamiento** | RAP Behavior Definition | Declarar operaciones, validaciones, determinaciones, acciones y eventos. |
| **Servicios** | RAP / CAP | Exponer operaciones y contratos API a partir de definiciones. |
| **Persistencia** | RAP / CAP | Adaptadores de acceso, transacciones y operaciones gestionadas cuando proceda. |
| **Reglas de negocio** | RAP / SAP Build | Motor de evaluación de reglas, condiciones y decisiones declarativas. |
| **Seguridad** | ABAP Authorization / CAP | Autenticación, autorizaciones declarativas y control de acceso. |
| **Presentación** | Fiori Elements | Metadatos de vistas, formularios, tablas, acciones y navegación. |
| **Procesos** | SAP Build Process Automation | Definición y ejecución de procesos mediante motores propios o adaptadores. |
| **Extensibilidad** | BAdI / CAP Extensions | Puntos de extensión, eventos y componentes personalizados. |
| **Integración** | Integration Suite | Conectores, adaptadores, transformaciones y orquestación entre sistemas. |
| **Herramientas** | ADT / SAP Build Code | Edición, comprobación, inspección, pruebas y gestión de definiciones. |

La tercera columna representa **capacidades genéricas, no módulos empresariales**.

### Relación entre aplicaciones, ARP e infraestructura

```text
┌────────────────────────────────────────────────────┐
│             APLICACIONES CONSUMIDORAS              │
│             Erbas · Solúcar · terceros             │
│  Definen entidades, reglas, procesos e interfaces  │
└─────────────────────────┬──────────────────────────┘
                          │ Contratos públicos
                          ▼
┌────────────────────────────────────────────────────┐
│                 PLATAFORMA ARP                     │
│  Diccionario       CDS / modelos                   │
│  Comportamientos   Reglas / decisiones             │
│  Servicios / API   Seguridad                       │
│  Metadatos UI      Extensibilidad                  │
└─────────────────────────┬──────────────────────────┘
                          │ Puertos y adaptadores
                          ▼
┌────────────────────────────────────────────────────┐
│           INFRAESTRUCTURA INTERCAMBIABLE           │
│ PHP · Java · .NET · Bases de datos · Motores externos │
└────────────────────────────────────────────────────┘
```

No necesitamos que ARP sea un único *runtime* universal. Podemos mantener una especificación común y proporcionar implementaciones independientes en PHP, Java y .NET. Esto exige separar rigurosamente la definición de una capacidad de su implementación técnica.

## 3. Dónde nos hemos desviado

### 3.1. Confundir la secuencia de construcción con la definición del producto

El diccionario era el primer componente. El siguiente paso previsto, `ARP-RES-001`, se había centrado inicialmente en recursos y campos escalares.

Desarrollarlo no es incorrecto. El problema aparece cuando el siguiente paso se decide simplemente por lo que falta en el componente anterior, sin comprobar su contribución al objetivo global.

### 3.2. Riesgo de construir otro framework CRUD

Un sistema que declara campos, los valida y proporciona operaciones CRUD resulta útil, pero no representa por sí solo una alternativa conceptual a ABAP + CDS + RAP/CAP.

Faltarían capacidades fundamentales: composición de modelos, comportamiento, reglas, extensibilidad y generación o ejecución de servicios a partir de definiciones.

### 3.3. Priorizar prematuramente la implementación

Las versiones, las ramas, la portabilidad entre lenguajes y la conformidad son importantes. Pero no deberían dominar el desarrollo antes de disponer de un recorrido funcional completo.

Que `ARP-DICT-001` esté validado en PHP, Java y .NET es un avance real. No se propone desecharlo ni convertirlo en el centro de ARP.

La desviación identificada es principalmente **de prioridades y de alcance funcional**, no necesariamente de calidad técnica del código.

## 4. Propuesta de MVP de ARP

No se propone reproducir todas las herramientas de SAP, sino completar un recorrido vertical:

1. **Diccionario funcional:** definir tipos, campos, estructuras, restricciones, valores predeterminados y referencias reutilizables.
2. **CDS básico:** definir entidades, relaciones, proyecciones, filtros y consultas sin depender de una base de datos concreta.
3. **Comportamiento declarativo:** definir operaciones, validaciones, determinaciones, acciones y puntos de extensión.
4. **Reglas de negocio:** declarar condiciones y decisiones simples, con posibilidad de recurrir a código específico para reglas complejas.
5. **Servicios automáticos:** exponer capacidades declaradas mediante API, sin escribir repetidamente controladores y operaciones estándar.
6. **Seguridad y autorizaciones:** aplicar políticas declarativas sobre recursos, operaciones y, cuando corresponda, registros y campos.
7. **Presentación declarativa:** permitir que un cliente, incluido Angular, construya interfaces mediante metadatos y componentes reutilizables.
8. **Extensibilidad:** permitir implementaciones propias de las aplicaciones sin modificar ARP.

Los procesos complejos, las integraciones avanzadas, el motor visual de reglas y otras capacidades pueden llegar posteriormente. Sus futuras incorporaciones no deben exigir rediseñar el núcleo.

## 5. Prueba de aceptación conceptual

Supongamos que un tercero quiere construir una aplicación para gestionar bibliotecas.

Debería poder:

- Definir una entidad `Libro`, con campos y relaciones.
- Establecer una proyección para consultar libros disponibles.
- Declarar una acción `prestar`.
- Configurar reglas de disponibilidad.
- Exponer los servicios correspondientes.
- Presentar la información en una interfaz.

**ARP proporciona los mecanismos técnicos y declarativos.** La aplicación aporta las definiciones y la lógica específica que no pueda expresarse declarativamente.

El mismo procedimiento debería servir para una aplicación sanitaria, industrial, administrativa o comercial, sin introducir en ARP ninguna noción de esos sectores.

Este es el criterio fundamental de aceptación.

## 6. Próximos pasos propuestos

**No continuar implementando `ARP-RES-001` sin revisar antes la arquitectura funcional completa.** Tampoco revertir el trabajo realizado ni abrir una nueva ronda de versiones.

1. Recuperar la especificación original y contrastarla con las decisiones posteriores.
2. Inventariar las capacidades reales de `arp-dotnet` y de las implementaciones PHP y Java, separando terminado, parcial y pendiente.
3. Establecer las dependencias entre diccionario, CDS, comportamiento, reglas, servicios y presentación.
4. Revisar si `ARP-RES-001` sigue siendo el paso correcto o necesita redefinirse.
5. Reorganizar el MVP alrededor de un ejemplo neutral que atraviese las capacidades principales.

### Principio adicional: declarativo, pero extensible mediante código

**ARP debe ser declarativo, pero no exclusivamente declarativo.** Las reglas y los modelos resuelven gran parte del trabajo repetitivo; para lo demás debe existir un modelo de programación y extensión claro. Sin él, acabaríamos creando un sistema de configuración limitado en vez de una plataforma de desarrollo.

## Conclusión

Debemos recuperar el diseño del producto antes de seguir programando. El diccionario fue un buen punto de partida; no debe determinar por sí solo qué acabará siendo ARP.

**La meta no es desarrollar un ERP más rápidamente. Es desarrollar una plataforma con la que se pueda construir cualquier aplicación empresarial más rápidamente, incluido un ERP.**
