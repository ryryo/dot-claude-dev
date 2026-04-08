import path from "node:path"
import { fileURLToPath } from "node:url"

import type { NextConfig } from "next"

const configDir = path.dirname(fileURLToPath(import.meta.url))

const nextConfig: NextConfig = {
  outputFileTracingRoot: configDir,
}

export default nextConfig
