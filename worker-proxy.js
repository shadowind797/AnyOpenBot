export default {
  async fetch(request, env, ctx) {
    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, x-goog-api-key",
        },
      });
    }

    // Build target URL — simple: path from request → generativelanguage.googleapis.com
    const url = new URL(request.url);
    const apiPath = url.pathname + url.search;
    const targetUrl = `https://generativelanguage.googleapis.com${apiPath}`;

    // Rotate API keys
    if (!env.GEMINI_API_KEYS) {
      return new Response(JSON.stringify({ error: "GEMINI_API_KEYS missing" }), {
        status: 500,
        headers: { "Content-Type": "application/json" },
      });
    }
    const keys = env.GEMINI_API_KEYS.split(",").map((k) => k.trim());
    const apiKey = keys[Math.floor(Math.random() * keys.length)];

    // Prepare headers
    const newHeaders = new Headers(request.headers);
    newHeaders.set("x-goog-api-key", apiKey);
    newHeaders.delete("host");

    // Forward
    const modifiedRequest = new Request(targetUrl, {
      method: request.method,
      headers: newHeaders,
      body: ["GET", "HEAD"].includes(request.method) ? null : request.body,
      redirect: "follow",
    });

    try {
      const response = await fetch(modifiedRequest);
      const newResponse = new Response(response.body, response);
      newResponse.headers.set("Access-Control-Allow-Origin", "*");
      return newResponse;
    } catch (error) {
      return new Response(
        JSON.stringify({
          error: "Proxy forwarding failed",
          target: targetUrl,
          details: error.message,
        }),
        {
          status: 502,
          headers: { "Content-Type": "application/json" },
        }
      );
    }
  },
};
