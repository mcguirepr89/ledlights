# Flask app to control IR LED lights

### Brand: i-Zoom | Model #: FL265006

---

- `ledlights.lircd.conf` provided for 
`/etc/lirc/lircd.conf.d/ledlights.lircd.conf`

- `./systemd/led_controller.service` and `Caddyfile` provided for `gunicorn`
deployment

   - Debian system needs `lircd` and you will need `pip install gunicorn`
