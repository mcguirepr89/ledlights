# Flask app to control IR LED lights

### Brand: i-Zoom | Model #: FL265006

---

- `ledlights.lircd.conf` provided for 
`/etc/lirc/lircd.conf.d/ledlights.lircd.conf`

- `./systemd/ledlights.service.example` and `Caddyfile` provided for `gunicorn`
deployment

   - Debian system needs `lircd` and you will need `pip install gunicorn`

- `mqttleds.py` provided for home automation POC with service file
