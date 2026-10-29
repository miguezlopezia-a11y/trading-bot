# Paper runner — nota de operación (propuesta, NO activada)

**Estado:** el runner se ejecuta manualmente, una pasada por invocación. NO hay
cron ni systemd activos (restricción: solo con confirmación explícita de Pablo).

## Qué hace cada ejecución

1. Descarga BTC-USD 5y/1d con yfinance (mismo origen que el backtest) y guarda
   snapshot CSV + sha256 + meta en `data/` (prefijo `paper_btc_usd_<timestamp>`).
2. Simula ma_cross con el backtester real (`run_backtest`: fills en next-open,
   SL/TP/gap, MTM diario H1). **Simulación pura — cero capacidad de orden real**
   (verificación estructural: `verificar_paper_no_dinero_real.py`).
3. Registra cada trade en el journal (decisión = "observacion", por dictamen
   walk-forward FRÁGIL).
4. Regenera `docs/paper_dashboard.html` (estado, últimos trades, equity vs
   buy&hold en SVG embebido, sin recursos externos).

## Journal

Backend activo: **SQLite local** (`data/paper_journal.db`) — decisión por
bloqueo, no por elección: el proyecto Supabase bunker-staging
(`bepmmqhakoaiswbgxkyc`) **no resuelve en DNS** (verificado 2026-10-06 desde
el VPS y desde red local; otros proyectos supabase.co sí resuelven y responden
desde el VPS, así que no es un problema de red). Las credenciales anónimas del
proyecto existen (`/root/trading-bot-env`, chmod 600, fuera del repo, extraídas
de `/opt/bunker/.env`) y el código mantiene el backend Supabase listo: en
cuanto el proyecto vuelva a existir/ser accesible, el probe automático lo
detectará y usará Supabase sin cambios de código. Dedupe idempotente por
(evento, fecha_dato, detalle) en ambos backends.

Pendiente de Pablo: reactivar/provisionar el proyecto Supabase bunker-staging,
o confirmar SQLite como journal definitivo de Fase 2.

## Propuesta de activación diaria (SIN activar)

```
# /etc/cron.d/trading-bot-paper — PROPUESTA, NO INSTALAR sin OK de Pablo
# 05:10 UTC diario: descarga, simula, journal, dashboard
10 5 * * * root cd /opt/trading-bot && ./venv/bin/python src/paper_runner.py >> /var/log/trading-bot-paper.log 2>&1
```

Alternativa systemd timer equivalente (misma condición: no activar).

## Modo

Observación (walk-forward dictamen: frágil). Ninguna señal se "aprueba"; el
runner solo registra y visualiza. Reevaluar el modo tras track record de paper
de varios meses.
