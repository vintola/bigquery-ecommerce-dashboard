# Cloudflare Worker — dashboard.alvintola.com

A small reverse proxy in front of the Streamlit Community Cloud app.

## Why it exists

Streamlit Community Cloud routes requests by the `Host` header. A plain
CNAME from `dashboard.alvintola.com` to `alvintola-retail-dashboard.streamlit.app`
returns:

```
HTTP/2 404
server: nginx
```

The Worker fixes this by fetching the app at its real hostname and returning
the response on the custom domain. It also:

- rewrites `Origin` / `Referer` so Streamlit's XSRF check passes
- preserves the `Upgrade: websocket` response so `/_stcore/stream` works
- rewrites same-origin `Location` headers back to the custom domain
- redirects `/` to the raw app path `/~/+/`, avoiding Streamlit's viewer shell

## Deploy

```bash
cd cloudflare-worker
npx --yes wrangler@latest deploy
```

Requires a Wrangler login that can edit the `alvintola.com` zone.

## Change the upstream app

Edit `APP_ORIGIN` in `wrangler.jsonc` and redeploy. The value must be the full
Streamlit app URL, for example:

```json
"vars": { "APP_ORIGIN": "https://alvintola-retail-dashboard.streamlit.app" }
```

## Notes

- The app is served at `/~/+/`. That is Streamlit's raw app path; it bypasses
  the Community Cloud viewer shell, which otherwise calls `share.streamlit.io`
  and breaks under a custom domain.
- Streamlit's session cookies are host-only, so they are stored for
  `dashboard.alvintola.com` and forwarded to the app by the Worker.
- If Streamlit changes its raw app path or auth flow, re-test
  `https://dashboard.alvintola.com/` and adjust `APP_PATH` or the redirect
  handling.
