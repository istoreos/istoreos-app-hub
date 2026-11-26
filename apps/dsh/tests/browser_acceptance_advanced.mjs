const authorization = process.env.DSH_TEST_AUTHORIZATION;
const baseUrl = process.env.DSH_TEST_BASE || "http://192.168.30.7:13080";
const cdpUrl = process.env.DSH_TEST_CDP || "http://127.0.0.1:9222";

if (!authorization) throw new Error("missing browser-test authorization");

const target = await fetch(`${cdpUrl}/json/new?about:blank`, { method: "PUT" }).then((response) => {
  if (!response.ok) throw new Error(`could not create browser target: ${response.status}`);
  return response.json();
});
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});

let nextId = 1;
const pending = new Map();
const documents = [];
const assets = [];

socket.addEventListener("message", (event) => {
  const message = JSON.parse(event.data);
  if (message.id) {
    const callback = pending.get(message.id);
    if (!callback) return;
    pending.delete(message.id);
    if (message.error) callback.reject(new Error(message.error.message));
    else callback.resolve(message.result);
    return;
  }
  if (message.method !== "Network.responseReceived") return;
  const { response, type } = message.params;
  if (!response.url.startsWith(baseUrl)) return;
  const path = new URL(response.url).pathname;
  if (type === "Document") documents.push(response.status);
  if (path.startsWith("/assets/")) assets.push({ path, status: response.status });
});

function command(method, params = {}) {
  const id = nextId++;
  socket.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
}

try {
  await command("Network.enable");
  await command("Network.clearBrowserCookies");
  await command("Network.setExtraHTTPHeaders", {
    headers: { Authorization: `Basic ${authorization}` },
  });
  await command("Page.enable");
  await command("Page.navigate", { url: `${baseUrl}/` });
  await new Promise((resolve) => setTimeout(resolve, 8000));

  const failed = assets.filter((asset) => asset.status !== 200);
  console.log(
    `FINAL_DSH_ADVANCED_BROWSER=${documents.includes(200) && assets.length >= 4 && failed.length === 0 ? "PASS" : "FAIL"}` +
      ` document=${documents.join(",")} assets=${assets.length} failed=${failed.length}`,
  );
  if (!documents.includes(200) || assets.length < 4 || failed.length) process.exitCode = 1;
} finally {
  socket.close();
  await fetch(`${cdpUrl}/json/close/${target.id}`).catch(() => undefined);
}
