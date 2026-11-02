# Tasks

## 1. Esquema y migraciones

- [x] 1.1 Agregar modelos SQLAlchemy de usuario y sesión y migración Alembic aditiva sobre C-02; verificar upgrade, esquema y repetición en PostgreSQL de prueba aislado.
- [x] 1.2 Agregar migración SQLite explícita y versionada que preserve C-01; probar esquema existente, repetición y que import/create_app/health no ejecutan DDL ni crean la base.

## 2. Credenciales y bootstrap

- [x] 2.1 Implementar derivación scrypt con sal única/versionada, comparación segura y validación de identificador/contraseña; cubrir contraseña correcta, incorrecta, hashes incompatibles y usuario inexistente con pruebas unitarias.
- [x] 2.2 Implementar repositorio de usuarios y comando bootstrap interactivo; verificar que sólo crea el primer Administrador, no muestra ni registra la contraseña y no la acepta por argumentos.

## 3. Sesiones y configuración

- [x] 3.1 Validar JWT_SECRETO y algoritmo permitido sin valores débiles; verificar secreto ausente, corto, marcador de ejemplo y clave válida.
- [x] 3.2 Implementar emisión/validación/revocación JWT respaldada por sesión persistida; probar expiración, firma inválida, logout, cuenta inactiva y fallo de almacenamiento en SQLite y PostgreSQL aislado.

## 4. API y autorización

- [x] 4.1 Implementar login, sesión actual y logout con respuestas genéricas y sin campos sensibles; probar 200/204, credenciales inválidas (401), token expirado/revocado (401) y contrato OpenAPI.
- [x] 4.2 Implementar gestión de usuarios exclusiva de Administrador; probar 401/403, roles permitidos, normalización/duplicados, baja/cambio de rol y revocación de sesiones.
- [x] 4.3 Proteger POST /turnos para Administrador/Recepción, conservar íntegros los errores y reglas de C-01 y mantener /health público; probar matriz completa, JSON inválido autorizado y que una petición no autorizada no abre/muta la agenda.

## 5. Integración y documentación

- [x] 5.1 Documentar configuración segura, migración de ambos motores y bootstrap inicial; ejecutar los comandos documentados en bases ficticias descartables y verificar que no haya credenciales por defecto.
- [x] 5.2 Actualizar KB03, README, OpenAPI, CHANGES y evidencia para reflejar la matriz aprobada y sólo lo verificado; comprobar que no se afirme acceso de Profesional.
- [x] 5.3 Ejecutar integración autenticada/concurrente contra PostgreSQL de prueba aislado, suite completa desde backend/, `pip check`, `openspec validate --all --strict` y `git diff --check`; registrar omisiones si alguna prueba real no se ejecuta.

## Workflow follow-up

- Archivar C-03 con sincronización de la capability nueva y del delta `alta-turnos` sólo después de que todas las tareas estén verificadas y el usuario haya aprobado la matriz de permisos.
