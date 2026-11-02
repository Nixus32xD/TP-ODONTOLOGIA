# Spec Delta

## Purpose

Permite al personal registrar movimientos monetarios manuales y consultar saldos exactos de forma trazable, sin conectar proveedores ni emitir comprobantes fiscales.

## ADDED Requirements

### Requirement: Registrar cargos manuales en ARS exactos
El sistema SHALL permitir a Administrador y Recepción registrar un cargo manual positivo para un paciente activo, con concepto breve y monto ARS exacto. El cargo SHALL ser inmutable y SHALL NOT generarse automáticamente desde turnos, prestaciones o planes.

#### Scenario: Cargo válido
- **GIVEN** Administrador o Recepción registra un cargo para un paciente activo con importe decimal válido
- **WHEN** confirma la operación con una clave de idempotencia
- **THEN** se crea un cargo inmutable en centavos y el saldo inicial coincide exactamente con el cargo

#### Scenario: Monto malformado o fuera de límite
- **GIVEN** el importe usa coma, signo, exponente, más de dos decimales, cero, valor negativo o supera ARS 999.999.999,99
- **WHEN** se solicita registrar el cargo
- **THEN** la API responde 422 sin redondear ni modificar cargo, saldo, idempotencia o auditoría

#### Scenario: Ficha inactiva o rol no permitido
- **GIVEN** la ficha está inactiva o la solicitud no pertenece a Administrador o Recepción
- **WHEN** se intenta crear el cargo
- **THEN** se rechaza sin crear movimientos ni exponer datos financieros

### Requirement: Registrar cobros parciales sin sobrepagar
El sistema SHALL permitir a Administrador y Recepción registrar cobros manuales positivos vinculados a un cargo. SHALL calcular el saldo como cargo menos cobros netos de reversiones y SHALL rechazar un cobro que exceda el saldo vigente.

#### Scenario: Cobro parcial y saldo derivado
- **GIVEN** un cargo pendiente por un monto exacto
- **WHEN** se registra un cobro menor al saldo
- **THEN** se agrega un movimiento inmutable y el saldo restante se calcula con centavos enteros

#### Scenario: Pago exacto o sobrepago
- **GIVEN** un cargo con saldo pendiente
- **WHEN** se registra un cobro igual al saldo o superior a éste
- **THEN** el pago exacto deja saldo cero y el sobrepago responde 409 sin cambiar el ledger

#### Scenario: Cobro sin cargo o sin acceso
- **GIVEN** un cargo inexistente o una sesión sin rol Administrador/Recepción
- **WHEN** se intenta registrar un cobro
- **THEN** la API responde 404 o 401/403 y no agrega movimientos

### Requirement: Revertir cobros con tope y motivo
El sistema SHALL permitir sólo a Administrador registrar reversiones append-only de un cobro, por importe positivo y no mayor al neto aún no revertido. Cada reversión SHALL conservar un motivo obligatorio y SHALL restaurar saldo sin editar o borrar movimientos previos.

#### Scenario: Reversión parcial o total
- **GIVEN** un cobro vigente con saldo reversible suficiente
- **WHEN** Administrador registra una reversión con motivo
- **THEN** se agrega un movimiento inmutable y el saldo del cargo aumenta por ese importe exacto

#### Scenario: Exceso concurrente o razón ausente
- **GIVEN** la suma solicitada supera el importe aún reversible o falta un motivo válido
- **WHEN** se intenta la reversión
- **THEN** se rechaza sin exceder el cobro, alterar saldos ni crear auditoría de éxito

#### Scenario: Recepción intenta revertir
- **GIVEN** una sesión válida de Recepción
- **WHEN** solicita una reversión
- **THEN** recibe 403 y el ledger conserva su estado

### Requirement: Consultar cuenta corriente derivada del ledger
El sistema SHALL permitir a Administrador y Recepción consultar cargos, cobros, reversiones y saldos por paciente en orden estable. Los importes SHALL exponerse como decimal de texto en ARS y el saldo SHALL derivarse de movimientos inmutables.

#### Scenario: Cuenta corriente
- **GIVEN** un paciente con cargos, cobros parciales y reversiones
- **WHEN** personal autorizado consulta sus movimientos
- **THEN** recibe cada movimiento y el saldo exacto derivado, sin valores binarios de punto flotante

#### Scenario: Acceso a cuenta corriente
- **GIVEN** una sesión ausente o con rol Profesional o Paciente
- **WHEN** consulta movimientos financieros
- **THEN** recibe 401/403 sin obtener cargos, cobros ni saldos

### Requirement: Hacer idempotentes los comandos monetarios
El sistema SHALL requerir una clave de idempotencia acotada por actor y tipo de comando. Una repetición con la misma clave y payload canónico SHALL devolver el resultado original; una clave reutilizada con payload distinto SHALL responder 409.

#### Scenario: Reintento de resultado confirmado
- **GIVEN** una operación monetaria ya confirmada cuya respuesta no llegó al cliente
- **WHEN** se repite con mismo actor, operación, clave y payload
- **THEN** se devuelve el resultado original sin crear otro movimiento ni evento

#### Scenario: Clave con payload distinto
- **GIVEN** existe una clave para un actor y tipo de operación con otro fingerprint
- **WHEN** se presenta la clave con un comando distinto
- **THEN** la API responde 409 y conserva el ledger

#### Scenario: Atomicidad de ledger y auditoría
- **GIVEN** falla la escritura de auditoría o idempotencia durante un comando válido
- **WHEN** termina la transacción
- **THEN** se revierten juntos el movimiento, el saldo derivado y el resultado idempotente

### Requirement: No procesar pagos ni emitir comprobantes reales
El sistema SHALL mantener los cargos, cobros y reversiones como registros manuales sintéticos. SHALL NOT enviar solicitudes a pasarelas, bancos o ARCA ni generar comprobantes fiscales.

#### Scenario: Operación desconectada
- **GIVEN** se registra un cargo, cobro o reversión en el demo local
- **WHEN** se confirma el movimiento
- **THEN** sólo se escribe el ledger local, sin llamadas externas ni identificadores fiscales
