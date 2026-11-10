# Política de seguridad

Eco guarda información sensible por naturaleza (qué haces en tu ordenador), así que la seguridad es prioritaria.

## Reportar una vulnerabilidad
**No abras un issue público.** Usa el reporte privado de GitHub:
<https://github.com/lizasodev/eco/security/advisories/new>

Intentaré responder en 7 días. Si el fallo se confirma, publicaré un parche y un aviso (advisory) con crédito, si lo deseas.

## Versiones soportadas
Solo la última versión publicada recibe correcciones.

## Modelo de amenazas
**Protege contra:** que otro usuario del sistema lea tu actividad; que secretos comunes acaben en disco; que datos salgan de tu máquina.

**Garantías de diseño**
- **Sin red:** Eco no abre ningún socket ni envía telemetría. Verifícalo: `grep -rn "socket\|urllib\|http" src/`.
- **Sin dependencias** de terceros en ejecución: menos superficie de ataque de cadena de suministro.
- **Permisos estrictos:** carpeta de datos `0700`, base de datos y ficheros `-wal/-shm` `0600`.
- **Filtrado antes de escribir:** lo que descarta `src/eco/privacy.py` nunca llega a disco.
- **`secure_delete`:** `eco forget` y `eco purge` sobrescriben el contenido borrado.
- **Sin ejecución de datos capturados:** los comandos guardados nunca se evalúan; las consultas FTS se sanean y se parametrizan (sin inyección SQL).

**NO protege contra:** malware o un atacante con tu mismo usuario o con root; acceso físico a un disco sin cifrar (usa cifrado de disco: LUKS); secretos que los filtros por patrón no reconozcan (los filtros son heurísticos, no infalibles).

## Recomendaciones
- Cifra tu disco (LUKS).
- Revisa y amplía `src/eco/privacy.py` con tus propios patrones.
- Ejecuta `eco purge --older-than 90d` periódicamente.
