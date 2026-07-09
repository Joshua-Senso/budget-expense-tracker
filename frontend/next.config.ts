import type { NextConfig } from "next"

const isDev = process.env.NODE_ENV === "development"
const apiOrigin = process.env.NEXT_PUBLIC_API_URL ?? ""
const authOrigin = process.env.NEXT_PUBLIC_AUTH_URL ?? ""

// No nonce/proxy-based CSP (docs/app/guides/content-security-policy.md):
// the (app) area is entirely client-rendered, and nonces require every page
// to opt into dynamic rendering, which would cost the public landing page
// its static optimization for no benefit here.
const cspHeader = `
  default-src 'self';
  script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""};
  style-src 'self' 'unsafe-inline';
  img-src 'self' blob: data:;
  font-src 'self';
  connect-src 'self' ${apiOrigin} ${authOrigin};
  object-src 'none';
  base-uri 'self';
  form-action 'self';
  frame-ancestors 'none';
  ${isDev ? "" : "upgrade-insecure-requests;"}
`
  .replace(/\s{2,}/g, " ")
  .trim()

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          // Superseded by the CSP `frame-ancestors` directive below, but kept
          // for browsers that don't support it (docs/.../headers.md).
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Content-Security-Policy", value: cspHeader },
        ],
      },
    ]
  },
}

export default nextConfig
