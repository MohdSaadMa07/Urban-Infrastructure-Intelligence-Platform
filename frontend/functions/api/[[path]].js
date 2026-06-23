const API_BACKEND = 'https://urban-infrastructure-intelligence-c000.onrender.com';

export async function onRequest(context) {
  try {
    const { request, env } = context;
    const backendUrl = env.RENDER_API_URL || API_BACKEND;
    const url = new URL(request.url);
    const target = new URL(url.pathname + url.search, backendUrl);

    const headers = new Headers(request.headers);
    headers.delete('host');
    headers.delete('content-length');

    const init = {
      method: request.method,
      headers,
    };

    if (!['GET', 'HEAD'].includes(request.method)) {
      const cloned = request.clone();
      init.body = await cloned.arrayBuffer();
    }

    const response = await fetch(target.toString(), init);
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: 'Proxy error', detail: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
