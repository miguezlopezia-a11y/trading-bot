U="https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1=0&period2=1762387200&interval=1d"
A='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
S="ssh -o BatchMode=yes -o ConnectTimeout=15 bunker"

printf 'sonda  hora       WSL            VPS\n'
i=1
while [ "$i" -le 8 ]; do
  w=$(curl -s -o /tmp/y_w.bin -w '%{http_code}:%{size_download}' --max-time 25 -A "$A" "$U" || printf 'ERR:0')
  v=$($S "curl -s -o /dev/null -w '%{http_code}:%{size_download}' --max-time 25 -A '$A' '$U'" 2>/dev/null || printf 'ERR:0')
  printf '%-6s %-10s %-14s %s\n' "$i" "$(date -u +%H:%M:%S)" "$w" "$v"
  i=$((i+1))
  sleep 15
done
