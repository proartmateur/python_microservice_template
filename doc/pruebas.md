# Pruebas y TDD

## Ejecutar e2e de users (sin limpiar DB)

Estas pruebas escriben en la base real y no eliminan registros fisicamente; solo validan el soft delete del endpoint.
Es altamente recomendado ejecutar las pruebas tal como se muestra, puesto que
se previene que en el flujo CI/CD las pruebas se ejecuten contra una base de datos de producción.

En PowerShell:

```bash
$env:RUN_E2E_USERS="1"
python -m uv sync --group dev
python -m uv run poe test_e2e_users
```

Alternativa si ya usas extras:

```bash
$env:RUN_E2E_USERS="1"
uv run poe test_e2e_users
```

## Test Driven Development TDD

El módulo está pensado para evolucionar, por tal motivo, 
refactorizar código o agregar nuevas funcionalidades es algo común. 
Para esto, se recomienda usar TDD, es decir, escribir primero las pruebas y luego el código de producción.

### ¡Las pruebas quitan tiempo!
Es verdad que escribir pruebas automatizadas consume tiempo.
Por tal motivo el módulo genera las pruebas E2E así solamente
nos preocupamos por escribir nuevo código y podemos validad que
nuestros cambios **NO** tengan efectos colaterales en el resto del módulo.