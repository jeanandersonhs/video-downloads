/** @type {import('next').NextConfig} */
const nextConfig = {
  // Em desenvolvimento (`next dev`), a API Python roda à parte: `uvicorn api.index:app --port 8787`.
  // Em produção a Vercel roteia /api/* para a função Python (ver vercel.json).
  async rewrites() {
    if (process.env.NODE_ENV !== "development") return [];
    const origin = process.env.API_ORIGIN ?? "http://127.0.0.1:8787";
    return [{ source: "/api/:path*", destination: `${origin}/api/:path*` }];
  },
};

export default nextConfig;
