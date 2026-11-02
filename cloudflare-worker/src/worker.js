/**
 * Reverse proxy for the Streamlit Community Cloud app.
 *
 * Streamlit routes by the Host header, so a plain CNAME to *.streamlit.app
 * returns 404. This Worker fetches the app by its real hostname and presents
 * it on the custom domain. The raw app path (/~/+/) is used deliberately so
 * the request never leaves the custom domain for Streamlit's viewer shell.
 * Origin/Referer are rewritten for Streamlit's XSRF check, and WebSocket
 * upgrades are passed through untouched.
 */

const DEFAULT_APP_ORIGIN = "https://alvintola-retail-dashboard.streamlit.app";
const APP_PATH = "/~/+/";

function targetOrigin(env) {
  return new URL(env.APP_ORIGIN || DEFAULT_APP_ORIGIN);
}

export default {
  async fetch(request, env) {
    const target = targetOrigin(env);
    const incoming = new URL(request.url);

    if (incoming.pathname === "/") {
      return Response.redirect(incoming.origin + APP_PATH, 302);
    }

    const upstream = new URL(incoming.pathname + incoming.search, target);

    const headers = new Headers(request.headers);
    if (headers.has("Origin")) {
      headers.set("Origin", target.origin);
    }
    const referer = headers.get("Referer");
    if (referer) {
      try {
        const ref = new URL(referer);
        headers.set("Referer", target.origin + ref.pathname + ref.search);
      } catch {
        // Ignore malformed referers.
      }
    }

    const isWebSocket =
      (request.headers.get("Upgrade") || "").toLowerCase() === "websocket";

    const response = await fetch(upstream, {
      method: request.method,
      headers,
      redirect: "manual",
      body:
        request.method === "GET" || request.method === "HEAD"
          ? undefined
          : request.body,
    });

    // Preserve the 101 response and its webSocket handle for Streamlit's
    // /_stcore/stream connection.
    if (isWebSocket) {
      return response;
    }

    const responseHeaders = new Headers(response.headers);
    const location = responseHeaders.get("Location");
    if (location) {
      try {
        const next = new URL(location, target);
        if (next.origin === target.origin) {
          responseHeaders.set(
            "Location",
            incoming.origin + next.pathname + next.search + next.hash,
          );
        }
      } catch {
        // Leave absolute redirects to other hosts alone.
      }
    }

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  },
};
