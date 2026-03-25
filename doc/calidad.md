# Comprobar la calidad del código

Dado que el módulo es parte de un microservicio de grado
empresarial, es importante mantener un código de alta calidad. 
Para esto, se recomienda usar herramientas de linting, formateo y chequeo de tipos.

Python es un lenguaje dinámico, lo que significa que no tiene un sistema de tipos estático como otros lenguajes. 
Sin embargo, existen herramientas como `mypy` que permiten realizar chequeo de tipos estático en Python. 
Esto ayuda a detectar errores de tipo antes de ejecutar el código, lo que mejora la calidad y la mantenibilidad del código.

## Linting

```bash
uv run poe lint
```
## Formatear código

```bash
uv run poe format
```

## Chequear tipos

```bash
uv run poe typecheck
```
