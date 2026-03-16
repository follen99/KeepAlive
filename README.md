## Build + Run con restart automatico

**Build dell'immagine:**
```bash
docker build -t nome-app .
```

**Run con restart policy:**
```bash
docker run -d \
  --name nome-app \
  --restart unless-stopped \
  -p 5000:5000 \
  -v $(pwd)/instance:/app/instance \
  nome-app
```

---

### Restart policy — opzioni chiave

| Policy | Comportamento |
|---|---|
| `no` | Mai (default) |
| `on-failure` | Solo su exit code != 0 |
| `always` | Sempre, anche dopo `docker stop` + daemon restart |
| `unless-stopped` | Come `always`, ma **non** riparte se stoppato manualmente ✅ |

Per la tua Flask app, **`unless-stopped`** è la scelta migliore.

---

### Avvio automatico al boot del sistema

Dipende dal sistema:

**systemd (Linux moderno):**
```bash
sudo systemctl enable docker   # Docker stesso si avvia al boot
```
Con `--restart unless-stopped` il container riparte automaticamente quando Docker si avvia.

**Verifica:**
```bash
docker inspect nome-app | grep RestartPolicy
```