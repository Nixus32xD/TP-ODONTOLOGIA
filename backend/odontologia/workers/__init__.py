"""Tareas asincrónicas con Redis — pendiente de C-17.

Estructura reservada para la cola de recordatorios: al confirmarse un
turno se encolará un recordatorio ficticio en Redis y un worker lo
procesará con un canal simulado (sin WhatsApp ni email reales).
Un fallo del recordatorio no debe duplicar ni borrar el turno.
"""
