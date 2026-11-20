# ARP — Modelo semántico y primera integración con Angular

**Fecha:** 15 de noviembre de 2026  
**Estado:** Documento de trabajo para revisión y cierre punto por punto.  
**Relación:** Desarrollo parcial del objetivo descrito en `ARP_reorientacion_arquitectura_funcional.md`.  
**Versionado:** No se asigna versión 0.1, ni se declara completo el MVP de ARP.

## 1. Propósito y alcance

Definir el **primer recorrido funcional vertical** de ARP: reutilizar el diccionario existente, obtener definiciones de almacenamiento, enriquecerlas mediante un modelo lógico, publicar proyecciones y consumirlas desde un cliente Angular.

Este recorrido **no es todo ARP ni su MVP definitivo**. Los demás puntos del documento de reorientación también tendrán que definirse, al menos en su parte básica, antes de fijar la primera versión global de producto. Después se revisarán, completarán y perfeccionarán de forma incremental hasta alcanzar un MVP realmente viable.

ARP no incluirá conceptos, estructuras ni operaciones empresariales predefinidos de ninguna aplicación consumidora.

## 2. Arquitectura conceptual acordada para este recorrido

```text
                    Diccionario ARP (existente)
                       tipos semánticos
                              │
Base de datos ──> Modelo físico generado (YAML por tabla)
                              │
                              ▼
                      Modelo lógico propio
            asociaciones, restricciones, literales
                              │
                              ▼
                     Proyecciones públicas
              campos, consultas, operaciones
                              │
                              ▼
                     Servicios del backend
                  validación y autorización
                              │
                              ▼
                     Cliente ARP / Angular
                 listados, formularios, acciones
```

El diagrama muestra una **cadena conceptual de enriquecimiento**, no una obligación de usar una base de datos, Angular o un CRUD para todos los consumidores de ARP.

### 2.1. Diccionario

`ARP-DICT-001` proporciona tipos escalares y restricciones intrínsecas reutilizables. No se reimplementará en CDS. Las propiedades contextuales de los campos (por ejemplo, obligatoriedad o nulabilidad de uso) deberán respetar la frontera que establezca el contrato correspondiente.

### 2.2. Modelo físico: generado y no editable

Cuando existe una base de datos relacional, ARP podrá extraer por tabla una definición YAML con los hechos físicos verificables: identificador de tabla y columna, tipo y capacidad física, nulabilidad, claves, índices y relaciones que el proveedor pueda demostrar.

- El **esquema físico real** es la autoridad sobre esos hechos; el YAML es un reflejo generado.
- La definición generada **no se modifica manualmente**.
- La generación puede repetirse sin perder configuraciones del usuario.
- Tras migraciones o cambios de esquema, se regeneran las definiciones afectadas y se comprueban sus dependencias.
- Una columna desaparecida o incompatible **no provoca el borrado silencioso** de las definiciones lógicas o proyecciones que la utilicen: se informa del problema.
- La actualización automática es un **objetivo funcional**. El mecanismo preciso de detección (migraciones, comprobación periódica, evento del proveedor, etc.) aún debe concretarse; no se presupone que todos los motores notifiquen cambios en tiempo real.

Ejemplo: una columna `TINYINT SIGNED` admite físicamente de `-128` a `127`. Este límite es un dato físico, no la regla funcional de la aplicación.

### 2.3. Modelo lógico: definido por el consumidor

La aplicación podrá asociar un campo físico a un elemento del diccionario, definir restricciones adicionales **compatibles con sus límites físicos**, aportar literales y añadir relaciones o metadatos semánticos que no se deducen de SQL.

Ejemplos:

- Una columna `VARCHAR(10)` se vincula al elemento `customer.code` del diccionario, sin que ARP deduzca automáticamente esa semántica del nombre de la columna.
- Una puntuación almacenada como `TINYINT SIGNED` se restringe lógicamente a `0..10`.

La capa lógica pertenece al consumidor y **no se sobrescribe** al regenerar el modelo físico. ARP debe comprobar las incompatibilidades conocidas sin fingir que una propiedad desconocida está verificada. Las transformaciones explícitas pueden requerir reglas de compatibilidad específicas.

### 2.4. Proyecciones: definidas por el consumidor

Sobre el modelo lógico se declararán proyecciones para distintos usos. Cada una podrá establecer campos expuestos, nombres y etiquetas de presentación, selección, relaciones navegables y operaciones permitidas.

Una proyección **no es necesariamente una vista SQL**. Es una definición lógica de consumo, que podrá usar distintas estrategias de consulta y ejecución.

Una proyección pública actuará como **lista explícita de datos expuestos**, aplicada por el backend. No sustituye el control de autorización; ambos deben cumplirse, también al filtrar, consultar relaciones o modificar datos.

### 2.5. Servicios y conexión con Angular

ARP debe permitir que las proyecciones proporcionen **contratos de servicio y metadatos** suficientes para que el cliente Angular construya listados y formularios genéricos sin conocer la tabla física ni el lenguaje del backend.

Las operaciones CRUD podrán declararse donde correspondan, pero **declarar una operación no equivale a autorizarla ni garantiza que pueda ejecutarse automáticamente**.

Se estudiarán dos formas de ejecución:

- **Delegada:** adaptadores a servicios y transacciones de la aplicación.
- **Gestionada:** operaciones estándar que ARP pueda ejecutar de forma segura cuando el modelo, las reglas y los adaptadores lo permitan.

**Pendiente de cierre:** alcance inicial de CRUD gestionado frente a delegado, identidad de registros, modificaciones parciales, concurrencia y transacciones. No se aprueba en este documento una generación indiscriminada de SQL o de operaciones de escritura.

Angular usará las definiciones publicadas y podrá aplicar restricciones de interfaz, pero **la validación, la autorización y la decisión final de persistencia siguen en el servidor**.

## 3. Prueba funcional del primer recorrido

Una aplicación de demostración, sin funcionalidades empresariales preinstaladas en ARP, deberá permitir:

1. Generar una definición física desde una tabla real y demostrar su regeneración tras una migración.
2. Asociar un campo físico a un elemento del diccionario y añadir una restricción lógica más estrecha que la física.
3. Detectar y comunicar una incompatibilidad introducida deliberadamente en el esquema.
4. Definir dos proyecciones distintas de la misma entidad lógica, con conjuntos de campos diferentes.
5. Exponer los metadatos necesarios para representarlas en Angular.
6. Consultar y, para una operación habilitada y autorizada, modificar datos reales sin omitir los controles del backend.
7. Comprobar que un campo excluido de la proyección no aparece en la respuesta del servidor, ni puede recuperarse por parámetros no autorizados.

Estas pruebas son **criterios para cerrar este tramo funcional**, no afirmaciones de implementación ya terminada.

## 4. Decisiones que siguen abiertas

| Cuestión | Estado |
|---|---|
| Representación neutral común a YAML y API tipadas | Por concretar |
| Vinculación física ↔ lógica y tratamiento de transformaciones | Por especificar |
| Mecanismo de detección y regeneración del esquema | Por elegir |
| Relación exacta entre entidad, vista, proyección y recurso público | Por formalizar |
| Operaciones CRUD gestionadas y delegadas | Principio admitido; alcance por decidir |
| Contratos de autorización, concurrencia y transacciones | Por especificar |
| Contrato de metadatos e interacción con Angular | Por concretar y probar |

## 5. Secuencia de trabajo y política de versiones

1. **Definir y probar este primer tramo** sin asignarle una versión de producto ni tratarlo como MVP completo.
2. **Continuar con los restantes bloques de la reorientación** hasta tener su alcance básico definido y disponer de una visión integrada de ARP.
3. **Evaluar el conjunto**, identificar vacíos y decidir entonces la primera base versionable.
4. **Pulir y evolucionar por versiones** las capacidades del conjunto hasta alcanzar un MVP viable, verificando integración y conformidad.

No se publicarán versiones por el mero hecho de terminar una capacidad aislada. La planificación de versiones no debe sustituir a la definición del producto.

---

**Criterio rector:** ARP aporta las herramientas y mecanismos declarativos; cada aplicación define su modelo y su comportamiento. Ninguna comodidad del primer recorrido debe convertir una base de datos relacional, un CRUD o Angular en requisitos universales de ARP.
