const backend = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
export default {
  async rewrites() { return [
    {source:'/api/:path*', destination:backend+'/api/:path*'},
    {source:'/ws/:path*', destination:backend+'/ws/:path*'},
    {source:'/static/:path*', destination:backend+'/static/:path*'},
  ]; },
  async redirects() { return [{source:'/test/:token', destination:'/flash/:token', permanent:false}]; },
  async headers() { return [{source:'/:path*',headers:[
    {key:'X-Content-Type-Options',value:'nosniff'},
    {key:'X-Frame-Options',value:'DENY'},
    {key:'Referrer-Policy',value:'no-referrer'},
    {key:'Permissions-Policy',value:'camera=(), microphone=(), geolocation=()'},
  ]}]; }
};
