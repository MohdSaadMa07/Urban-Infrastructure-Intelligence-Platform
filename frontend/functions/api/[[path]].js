const API_BACKEND = typeof RENDER_API_URL !== 'undefined'
  ? RENDER_API_URL
  : 'https://urban-infrastructure-intelligence-c000.onrender.com';

export async function onRequest(context) {
  const { request, env } = context;
  const backendUrl = env.RENDER_API_URL || API_BACKEND;
  const url = new URL(request.url);
  const target = new URL(url.pathname + url.search, backendUrl);

  const headers = new Headers(request.headers);
  headers.delete('host');

  const init = {
    method: request.method,
    headers,
  };

  if (!['GET', 'HEAD'].includes(request.method)) {
    init.body = request.body;
  }

  return fetch(target, init);
}
