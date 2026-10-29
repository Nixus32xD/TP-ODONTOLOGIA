"""Autenticación con JWT — pendiente de C-03 (governance CRÍTICO).

Estructura reservada para emitir y validar tokens JWT de personal
(recepción, profesional, administración) y proteger POST /turnos.
La matriz de permisos y el contrato deben aprobarse en Propose antes de
escribir código de seguridad. El secreto JWT se leerá del entorno y nunca
se versiona.
"""
