/**
 * Serveur de developpement dentist237 — zero dependance.
 *
 *   npm run dev   ->  http://localhost:5173
 *
 * Reconstruit le site a chaque modification de src/, styles.css ou main.js,
 * puis rafraichit le navigateur via SSE. Volontairement sans paquet npm :
 * le projet livre est du HTML statique, il ne doit pas trainer un
 * node_modules derriere lui.
 */

import { createServer } from "node:http";
import { spawn, spawnSync } from "node:child_process";
import { readFile, stat } from "node:fs/promises";
import { watch } from "node:fs";
import { join, extname, resolve } from "node:path";

const ROOT = resolve(import.meta.dirname);
const PORT = Number(process.env.PORT) || 5173;

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".xml": "application/xml; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".webp": "image/webp",
  ".woff2": "font/woff2",
  ".txt": "text/plain; charset=utf-8",
};

/* ---- Python : "python" sur Windows, "python3" ailleurs ---- */
const PY = (() => {
  for (const cmd of ["python", "python3"]) {
    const r = spawnSync(cmd, ["--version"], { stdio: "ignore" });
    if (r.status === 0) return cmd;
  }
  console.error("[dev] python introuvable — build.py ne peut pas tourner.");
  process.exit(1);
})();

/* ---- Reconstruction ---- */
let building = false;
let queued = false;

function build(reason = "") {
  if (building) { queued = true; return; }
  building = true;
  const t = Date.now();
  const p = spawn(PY, ["build.py"], { cwd: ROOT });
  let err = "";
  p.stderr.on("data", (d) => (err += d));
  p.on("close", (code) => {
    building = false;
    if (code === 0) {
      console.log(`[dev] build ok en ${Date.now() - t}ms ${reason}`);
      reload();
    } else {
      console.error(`[dev] build ECHEC\n${err}`);
    }
    if (queued) { queued = false; build(reason); }
  });
}

/* ---- Live reload (SSE) ---- */
const clients = new Set();
function reload() {
  for (const res of clients) res.write("data: reload\n\n");
}

const SNIPPET = `<script>
new EventSource("/__dev").onmessage=()=>location.reload();
</script>`;

/* ---- Serveur ---- */
const server = createServer(async (req, res) => {
  const url = decodeURIComponent(req.url.split("?")[0]);

  if (url === "/__dev") {
    res.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    });
    res.write("retry: 1000\n\n");
    clients.add(res);
    req.on("close", () => clients.delete(res));
    return;
  }

  // /soins/ -> soins/index.html
  let file = join(ROOT, url);
  try {
    if ((await stat(file)).isDirectory()) file = join(file, "index.html");
  } catch {
    if (!extname(url)) file = join(ROOT, url, "index.html");
  }

  try {
    let body = await readFile(file);
    const type = TYPES[extname(file)] || "application/octet-stream";
    if (type.startsWith("text/html")) {
      body = Buffer.from(body.toString("utf8").replace("</body>", SNIPPET + "</body>"));
    }
    res.writeHead(200, { "Content-Type": type, "Cache-Control": "no-store" });
    res.end(body);
  } catch {
    res.writeHead(404, { "Content-Type": "text/html; charset=utf-8" });
    res.end(`<pre style="font:14px/1.6 monospace;padding:2rem">404 — ${url}
Pages disponibles : /  /soins/  /tarifs/  /urgences/  /cabinets/
/contact/  /rendez-vous/  /a-propos/  /mentions-legales/</pre>${SNIPPET}`);
  }
});

/* ---- Surveillance ---- */
let timer;
for (const target of ["src", "styles.css", "main.js", "build.py"]) {
  try {
    watch(join(ROOT, target), { recursive: true }, (_e, name) => {
      clearTimeout(timer);
      timer = setTimeout(() => build(`(${name || target})`), 80);
    });
  } catch { /* cible absente : on ignore */ }
}

build("(initial)");
server.listen(PORT, () => {
  console.log(`\n  dentist237 — dev\n  http://localhost:${PORT}\n`);
});
