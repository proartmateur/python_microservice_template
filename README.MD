# Proyecto base para API REST y microservicios con Python

## Tabla de contenidos
- Arquitectura [arquitectura.md](doc/arquitectura.md)
- Instalación y uso [instalacion.md](doc/instalacion.md)
- Pruebas y TDD [pruebas.md](doc/pruebas.md)
- Calidad del código [calidad.md](doc/calidad.md)
- Migraciones de base de datos [migraciones_db.md](doc/migraciones_db.md)

## ¿Cómo crear un nuevo módulo?

```bash
.\gen.exe -m <nombre_modulo> <props:types>
```

### Ejemplo

```bash
.\gen.exe -m cosa name:str,is_phisical:bool
```