/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    let backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
    
    // Ensure the backend URL starts with a protocol to prevent Next.js build errors
    if (!backendUrl.startsWith('http://') && !backendUrl.startsWith('https://')) {
      const isLocal = backendUrl.includes('localhost') || backendUrl.includes('127.0.0.1');
      backendUrl = `${isLocal ? 'http://' : 'https://'}${backendUrl}`;
    }

    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
