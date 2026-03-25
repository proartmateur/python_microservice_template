# Arquitectura del template de dos capas

Este template de microservicio está diseñado con una arquitectura de dos capas, que se compone de:


## ¿Qué se entiende por CAPA en este diseño?

Una capa es un nivel de abstracción que agrupa componentes relacionados con una función específica dentro del microservicio.

Puede contener uno o varios archivos, dentro de una arquitectura muy simple,  suele usarse un archivo por capa.

Este diseño está pensado para ser extendido fácilmente y para ser probado (**TDD**), por tal motivo se dividieron las capas
en varios archivos que permiten una mejor organización y mantenibilidad del código.

Más archivos no implica mayor dificultad de programación. Cada archivo busca ser granular y corto. Así tenemos pequeñas piezas
tipo LEGO que se pueden ensamblar y mezclar de diversas formas para crear nuevas funcionalidades sin necesidad de modificar código existente.

El diseño es una simplificación de la arquitectura Ports & Adapters (Hexagonal), además de tener inspiración en
frameworks como Rails (ruby) o Laravel (php). Se espera que esta mezcla de patrones y estilos sea fácil de entender y aplicar para la mayoría 
de los programadores, sin necesidad de aprender un nuevo patrón o estilo de arquitectura.

![MVC Microservicio-MVC Escalable 2 capas.drawio.png](MVC%20Microservicio-MVC%20Escalable%202%20capas.drawio.png)

## Capa de Dominio

Esta capa contiene la lógica de negocio y las reglas de negocio del microservicio. 
Es el corazón del microservicio, donde se definen los conceptos y las operaciones que se pueden realizar sobre ellos.

### Pros:
Para un módulo 100% CRUD, esta capa podría ser un mapeo para lanzar un evento de dominio, o ser ignorada por completo.
Sin embargo tenerla desde la primer generación del módulo, permite agregar lógica de negocio a medida que el módulo evoluciona, sin necesidad de modificar código existente, solo agregando nuevas piezas tipo LEGO.

### Contras
Solamente para módulos 100% CRUD, dejarla tal como se genera, podría ser una violación al principio **YAGNI**.
Solamente si es sabido que el módulo jamás va a tener lógica de negocio, entonces se podría omitir esta capa, pero es difícil saberlo desde el inicio, y es fácil agregarla después si se necesita.

## Capa de Infraestructura
Esta capa contiene la implementación de los detalles técnicos y tecnológicos del microservicio, 
como la persistencia de datos, la comunicación con otros servicios, la autenticación, etc.

Es importante separar esta capa de la capa de dominio, para evitar que los detalles técnicos afecten la lógica de negocio y para facilitar el mantenimiento y la evolución del microservicio.
En caso de que alguna de las dependencias de esta capa necesite ser cambiada, solo se tendría que modificar el código de esta capa, sin afectar la lógica de negocio ni el resto del microservicio.


## Organización de los archivos
Cada capa tiene su propia carpeta, y dentro de cada carpeta se organizan los archivos según su función y responsabilidad. 
Por ejemplo, en la capa de dominio, se pueden tener archivos para los modelos de dominio que para evitar confusión 
con el concepto del ORM llamaremos **Entidades de Dominio**, los servicios, los eventos de dominio, etc. 
En la capa de infraestructura, se pueden tener archivos para los repositorios, los adaptadores, los controladores, etc.

![MVC Microservicio_module.png](MVC%20Microservicio_module.png)

## Filosofía del template
- **Simplicidad**: El template busca ser lo más simple posible, sin sacrificar la funcionalidad ni la escalabilidad.
- **Extensibilidad**: El template está diseñado para ser extendido fácilmente, permitiendo agregar nuevas funcionalidades sin necesidad de modificar código existente.
- **Mantenibilidad**: El template busca ser fácil de mantener, con una organización clara y una separación de responsabilidades entre las capas.
- **Testabilidad**: El template está diseñado para ser probado fácilmente, con una estructura que facilita la creación de pruebas unitarias, de integración y End to End E2E.
- **Buenas prácticas**: El template sigue buenas prácticas de desarrollo, como el uso de patrones de diseño, la separación de responsabilidades, la modularidad, etc.

### Principios de desarrollo aplicados
- **DRY**: Don't Repeat Yourself, evitar la duplicación de código.
- **YAGNI***: You Ain't Gonna Need It, no agregar funcionalidades que no se necesitan.
- **KISS**: Keep It Simple, Stupid, mantener el código simple y fácil de entender.
- **SOLID**: Principios de diseño orientado a objetos, como la responsabilidad única, la apertura/cierre, la sustitución de Liskov, la segregación de interfaces y la inversión de dependencias.