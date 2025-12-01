import { NextResponse } from "next/server"
import fs from "fs"
import path from "path"

export async function GET() {
  const ts = new Date().toISOString()
  const projectRoot = path.resolve(process.cwd())
  const staticDir = path.join(projectRoot, ".next", "static")
  const staticExists = fs.existsSync(staticDir)

  return NextResponse.json({
    ok: true,
    timestamp: ts,
    static_exists: staticExists,
    cwd: projectRoot,
  })
}
