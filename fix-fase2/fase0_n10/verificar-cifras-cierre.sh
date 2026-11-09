printf -- '--- 1. URTH: de donde sale la discrepancia 11,8049 contra 12,111 ---\n'
python3 -I - <<'PY'
import json, time, urllib.request
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
req = urllib.request.Request(
    f"https://query1.finance.yahoo.com/v8/finance/chart/URTH?period1=0&period2={int(time.time())}&interval=1d",
    headers=UA)
d = json.load(urllib.request.urlopen(req, timeout=60))["chart"]["result"][0]
ts = d["timestamp"]
cl = d["indicators"]["quote"][0]["close"]
aj = d["indicators"]["adjclose"][0]["adjclose"]
f = lambda t: time.strftime("%Y-%m-%d", time.gmtime(t))
print(f"  velas={len(ts)}  {f(ts[0])} -> {f(ts[-1])}")
print(f"  bruto    close[0]={cl[0]} adjclose[0]={aj[0]}  close[-1]={cl[-1]} adjclose[-1]={aj[-1]}")
pares = [(t, c, a) for t, c, a in zip(ts, cl, aj) if c and a]
print(f"  sin nulos  n={len(pares)}  {f(pares[0][0])} -> {f(pares[-1][0])}")
print(f"             close {pares[0][1]} -> {pares[-1][1]}   adjclose {pares[0][2]} -> {pares[-1][2]}")
anos = (pares[-1][0] - pares[0][0]) / 86400 / 365.25
print(f"  anos={anos:.6f}")
print(f"  CAGR close    = {((pares[-1][1]/pares[0][1])**(1/anos)-1)*100:.6f} %")
print(f"  CAGR adjclose = {((pares[-1][2]/pares[0][2])**(1/anos)-1)*100:.6f} %")
anos_k = 14.814815
print(f"  con SU ventana de {anos_k} anos y SUS extremos 38.2197 -> 199.630005:")
print(f"             = {((199.630005/38.2197)**(1/anos_k)-1)*100:.6f} %")
PY

printf -- '--- 2. el DFR del BCE, de fuente primaria ---\n'
curl -s --max-time 25 'https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.DFR.LEV?lastNObservations=2&format=csvdata' \
  | awk -F, 'NR>1 {print "  fecha=" $9 "  DFR=" $10 " %"}'

printf -- '--- 3. sus cifras pegadas contra sus propios JSON ---\n'
cd /home/pablo/trading-bot-gh/.worktrees/n10/fix-fase2/fase0_n10 || exit 1
python3 -I - <<'PY'
import json
for f in ["salida_cierre_a2_granularidad.json", "salida_cierre_a5_ajuste_y_urth.json",
          "salida_cierre_a6_dfr_sg.json", "salida_cierre_bc_recalculo.json",
          "salida_cierre_a3_series_y_huecos.json", "salida_cierre_a4_stooq_fred.json"]:
    try:
        d = json.load(open(f))
        print(f"  {f:44} OK  claves={len(d) if isinstance(d, dict) else 'lista'}")
    except Exception as e:
        print(f"  {f:44} FALLO {type(e).__name__}: {e}")
PY
printf -- '--- 4. las tres cifras clave, extraidas de sus JSON ---\n'
grep -o -E '"(cagr[^"]*|CAGR[^"]*)"[^,}]*' salida_cierre_a5_ajuste_y_urth.json | head -6
grep -o -E '2\.500|2,500' salida_cierre_a6_dfr_sg.json | head -2
grep -o -E '"limpias"[^]]*.' salida_cierre_bc_recalculo.json | head -2
