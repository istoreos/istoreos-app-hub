var D = (r, b, y) => new Promise((a, i) => {
  var u = (n) => {
    try {
      p(y.next(n));
    } catch (q) {
      i(q);
    }
  }, e = (n) => {
    try {
      p(y.throw(n));
    } catch (q) {
      i(q);
    }
  }, p = (n) => n.done ? a(n.value) : Promise.resolve(n.value).then(u, e);
  p((y = y.apply(r, b)).next());
});
import { defineAsyncComponent as ve, h as j, computed as R, ref as J, onMounted as qe, onUnmounted as xe, openBlock as k, createElementBlock as C, unref as o, normalizeClass as G, createElementVNode as s, createTextVNode as h, toDisplayString as l, createBlock as ye, resolveDynamicComponent as be, withCtx as he, createCommentVNode as L, reactive as we } from "/luci-static/quickstart/card-runtime-v1.js";
const ke = '[data-fastnet-card]{--fn-down:var(--qs-card-accent);position:relative;isolation:isolate;gap:14px;background:linear-gradient(145deg,transparent 48%,#7b9ee909);border-radius:inherit}[data-fastnet-card] .qs-card-header h2>svg{color:var(--fn-down)}[data-fastnet-card] .qs-card-primary{background:var(--qs-card-accent);color:var(--qs-card-panel);border-color:transparent;padding:6px 13px;border-radius:9px;font-weight:600}[data-fastnet-card] .qs-card-menu>summary{border-color:transparent;color:var(--qs-card-muted)}[data-fastnet-card] .fn-speed-stage{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:center;gap:14px;padding:18px 20px;border-radius:14px;border:1px solid var(--qs-card-line);background:linear-gradient(120deg,#608ee90c,transparent 75%),var(--qs-card-soft)}[data-fastnet-card] .fn-speed-caption{display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:10px;letter-spacing:.7px;color:var(--qs-card-muted)}[data-fastnet-card] .fn-live{display:flex;align-items:center;gap:5px;letter-spacing:0;white-space:nowrap}[data-fastnet-card] .fn-live:before{content:"";width:5px;height:5px;border-radius:50%;background:var(--qs-card-muted)}[data-fastnet-card] .fn-live.is-active{color:var(--qs-card-accent)}[data-fastnet-card] .fn-live.is-active:before{background:currentColor;box-shadow:0 0 0 3px #6794ef20}[data-fastnet-card] .qs-card-metrics{gap:18px;align-items:center;grid-template-columns:1.25fr 1fr}[data-fastnet-card] .qs-card-metrics strong{font-size:clamp(30px,3.5vw,52px);line-height:1.15;letter-spacing:-1.7px;font-weight:700;margin-top:4px;color:var(--fn-down)}[data-fastnet-card] .qs-card-metrics>div+div{border-left:1px solid var(--qs-card-line);padding-left:18px}[data-fastnet-card] .qs-card-metrics>div+div strong{font-size:clamp(25px,2.5vw,36px);color:var(--qs-card-text);letter-spacing:-.9px}[data-fastnet-card] .qs-card-metrics small{letter-spacing:0}[data-fastnet-card] .qs-card-time{gap:5px;font-size:10px}[data-fastnet-card] .qs-card-statuses{padding:0;border:0;gap:10px}[data-fastnet-card] .qs-card-statuses>div{padding:10px 12px;border:1px solid var(--qs-card-line);border-radius:10px;background:var(--qs-card-panel)}[data-fastnet-card] .qs-card-statuses span{display:flex;align-items:center;gap:6px;letter-spacing:.3px;margin-bottom:3px}[data-fastnet-card] .qs-card-statuses i{width:6px;height:6px;border-radius:50%;background:var(--qs-card-muted)}[data-fastnet-card] .qs-card-statuses [data-tone=good] i{background:var(--qs-card-good)}[data-fastnet-card] .qs-card-statuses [data-tone=warning] i{background:var(--qs-card-warning)}[data-fastnet-card] .qs-card-footer{margin-top:0;align-items:center;font-size:10px}[data-fastnet-card] .qs-card-footer>span{display:flex;align-items:center;gap:6px}[data-fastnet-card] .fn-route-dot{width:5px;height:5px;border:1px solid var(--qs-card-muted);border-radius:50%}[data-fastnet-card] .qs-card-footer small{letter-spacing:1.5px;font-size:9px}[data-fastnet-card].qs-card-summary{gap:3px;background:none}[data-fastnet-card].qs-card-summary .fn-speed-stage{display:block;flex:none;padding:0;border:0;background:none}[data-fastnet-card].qs-card-summary .fn-speed-caption{display:none}[data-fastnet-card].qs-card-summary .qs-card-metrics{grid-template-columns:1fr 1fr;gap:12px}[data-fastnet-card].qs-card-summary .qs-card-metrics strong{font-size:23px;letter-spacing:-.5px;margin:0}[data-fastnet-card].qs-card-summary .qs-card-metrics>div+div{padding:0;border:0}[data-fastnet-card].qs-card-summary .qs-card-statuses>div{padding:0;border:0;background:none;max-width:50%}[data-fastnet-card].qs-card-summary .qs-card-statuses span{margin:0;gap:4px}[data-fastnet-card].qs-card-summary .qs-card-statuses i{width:4px;height:4px}[data-fastnet-card].qs-card-summary .qs-card-primary{padding:2px 7px;border-radius:6px}@media(max-width:600px){[data-fastnet-card]:not(.qs-card-summary) .fn-speed-stage{padding:14px;gap:12px}[data-fastnet-card]:not(.qs-card-summary) .qs-card-metrics strong{font-size:36px}[data-fastnet-card]:not(.qs-card-summary) .qs-card-metrics>div+div strong{font-size:28px}}[data-fastnet-card].fn-dense:not(.qs-card-summary){gap:6px;padding:12px 16px}[data-fastnet-card].fn-dense:not(.qs-card-summary) .fn-speed-stage{padding:10px 12px;gap:6px}[data-fastnet-card].fn-dense:not(.qs-card-summary) .fn-speed-caption{display:none}[data-fastnet-card].fn-dense:not(.qs-card-summary) .qs-card-metrics strong{font-size:32px;line-height:1.15;margin:0}[data-fastnet-card].fn-dense:not(.qs-card-summary) .qs-card-metrics>div+div strong{font-size:27px}[data-fastnet-card].fn-dense:not(.qs-card-summary) .qs-card-statuses>div{padding:6px 9px}[data-fastnet-card].fn-dense:not(.qs-card-summary) .qs-card-footer{display:none}.fn-lan-summary{display:grid;grid-template-columns:1fr auto;gap:3px 8px;font-size:10px;color:var(--qs-card-muted);border-top:1px solid var(--qs-card-line);padding-top:8px}.fn-lan-summary strong{font-size:12px;font-weight:500;color:var(--qs-card-text);white-space:nowrap}.fn-lan-summary small{font-size:9px;font-weight:400}.fn-lan-summary time{grid-column:1/-1;font-size:10px}.qs-card-summary .fn-lan-summary{padding-top:2px;border:0;gap:1px}.qs-card-summary .fn-lan-summary time{display:none}', _ = (r) => r && ["running", "cancel_requested"].includes(r.state), K = ["running", "cancel_requested", "succeeded", "partial", "failed", "cancelled", "interrupted"];
function _e(r) {
  var b, y, a, i;
  if ((r == null ? void 0 : r.schemaVersion) !== 1 || !["ready", "disabled", "unavailable"].includes((b = r.service) == null ? void 0 : b.state) || !("latest" in r) || !("task" in r)) throw Error("invalid_summary");
  if ((y = r.latest) != null && y.bandwidth) {
    const u = r.latest.bandwidth;
    if (![u.downloadBps, u.uploadBps].every((e) => typeof e == "number" && Number.isFinite(e) && e >= 0) || !u.measuredAt || !Number.isFinite(Date.parse(u.measuredAt))) throw Error("invalid_bandwidth");
  }
  if (r.task && !K.includes(r.task.state)) throw Error("invalid_task");
  for (const u of ["download", "upload", "nat", "ipv6"]) if (r.latest) {
    const e = r.latest[u];
    if (!e || !["ok", "unavailable", "error", "not_tested"].includes(e.status) || e.value !== null && (["download", "upload"].includes(u) ? typeof e.value != "number" || !Number.isFinite(e.value) || e.value < 0 : typeof e.value != "string")) throw Error("invalid_measurement");
  }
  for (const u of ["download", "upload", "lanDownload", "lanUpload", "lanPing"]) {
    const e = (i = (a = r.latestResults) == null ? void 0 : a[u]) == null ? void 0 : i.value;
    if (e != null && (!Number.isFinite(e) || e < 0)) throw Error("invalid_measurement");
  }
  return r;
}
function Ae(r) {
  var a, i;
  const b = r == null ? void 0 : r.latestResults;
  if (b != null && b.download || b != null && b.upload) {
    const u = b.download, e = b.upload;
    return { downloadBps: (a = u == null ? void 0 : u.value) != null ? a : null, uploadBps: (i = e == null ? void 0 : e.value) != null ? i : null, measuredAt: [u == null ? void 0 : u.measuredAt, e == null ? void 0 : e.measuredAt].filter(Boolean).sort().pop(), mixed: !!(u && e && u.runId !== e.runId) };
  }
  const y = r == null ? void 0 : r.latest;
  return y ? y.bandwidth || { downloadBps: y.download.status === "ok" ? y.download.value : null, uploadBps: y.upload.status === "ok" ? y.upload.value : null, measuredAt: y.measuredAt } : null;
}
function E(r) {
  return r == null ? "—" : r > 0 && r < 1e5 ? "<0.1" : (r / 1e6).toLocaleString("en-US", { maximumFractionDigits: r >= 1e8 ? 0 : 1 });
}
function H(r, b) {
  return !r || !Number.isFinite(Date.parse(r)) ? "—" : new Date(r).toLocaleString(b === "en" ? "en-GB" : "zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: !1 });
}
const Ce = (r) => !!(r && Date.now() - Date.parse(r) > 864e5);
function Se(r, b = (a) => a, y = globalThis) {
  const a = b({ loading: !1, summary: null, task: null, submitting: !1, cancelling: !1, error: "", errorAction: "read", paused: !1, failures: 0 });
  let i = !0, u = !0, e, p, n, q = null, g = 0;
  const w = () => {
    y.clearTimeout(e), e = void 0, p == null || p.abort(), p = void 0, g++;
  }, N = (c) => [401, 403].includes(c == null ? void 0 : c.status) ? "permission" : (c == null ? void 0 : c.status) === 404 ? "upgrade" : "unavailable", S = () => {
    i && u && !a.paused && (e = y.setTimeout(_(a.task) ? V : A, _(a.task) ? 2e3 : 15e3));
  };
  function V() {
    return D(this, null, function* () {
      if (!i || !u || !_(a.task)) return;
      const c = a.task.id, f = ++g;
      p = new AbortController();
      try {
        const m = yield r.request("/task?id=" + encodeURIComponent(c), { signal: p.signal });
        if (!i || f !== g) return;
        if (m.id !== c || !K.includes(m.state)) throw Error("invalid_task");
        if (a.task = m, a.failures = 0, a.error = "", !_(m)) {
          q = null, yield A();
          return;
        }
      } catch (m) {
        if (!i || f !== g) return;
        a.failures++, a.error = N(m), a.errorAction = "read", (a.failures >= 3 || ["permission", "upgrade"].includes(a.error)) && (a.paused = !0);
      } finally {
        i && f === g && (p = void 0, S());
      }
    });
  }
  function A() {
    return D(this, null, function* () {
      if (w(), !i || !u) return;
      const c = g;
      a.loading = !0, p = new AbortController();
      try {
        const f = _e(yield r.request("/summary", { signal: p.signal }));
        if (!i || c !== g) return;
        a.summary = f, a.task = f.task || f.lastTask || null, a.error = "", a.failures = 0, a.paused = !1, _(a.task) && (q = null);
      } catch (f) {
        i && c === g && (a.error = N(f), a.errorAction = "read", a.failures++, a.paused = a.failures >= 3 || ["permission", "upgrade"].includes(a.error));
      } finally {
        i && c === g && (a.loading = !1, p = void 0, S());
      }
    });
  }
  function U() {
    return D(this, null, function* () {
      var f;
      if (!i || a.error === "permission" || a.submitting || _(a.task) || a.loading || ((f = a.summary) == null ? void 0 : f.service.state) !== "ready") return;
      w();
      const c = g;
      a.submitting = !0, a.error = "", n = new AbortController(), q || (q = Array.from(crypto.getRandomValues(new Uint8Array(16)), (m) => m.toString(16).padStart(2, "0")).join(""));
      try {
        const m = yield r.request("/run", { method: "POST", body: JSON.stringify({ idempotencyKey: q }), signal: n.signal });
        if (!i) return;
        if (!K.includes(m.state)) throw Error("invalid_task");
        if (q = null, c !== g) return;
        a.task = m, a.paused = !1, a.failures = 0, _(m) ? S() : yield A();
      } catch (m) {
        if (!i || c !== g) return;
        (m == null ? void 0 : m.status) === 409 ? (q = null, yield A()) : (a.error = N(m), a.errorAction = ["permission", "upgrade"].includes(a.error) ? "read" : "run", m != null && m.status && m.status < 500 && (q = null));
      } finally {
        i && (a.submitting = !1, n = void 0);
      }
    });
  }
  function O() {
    return D(this, null, function* () {
      if (!i || !_(a.task) || a.cancelling) return;
      w();
      const c = g;
      a.cancelling = !0, n = new AbortController();
      try {
        const f = yield r.request("/cancel", { method: "POST", body: JSON.stringify({ id: a.task.id }), signal: n.signal });
        if (!i || c !== g) return;
        a.task = f, _(f) ? S() : yield A();
      } catch (f) {
        i && c === g && (a.error = N(f), a.errorAction = "read", S());
      } finally {
        i && (a.cancelling = !1, n = void 0);
      }
    });
  }
  return { state: a, start: U, stop: O, reload: A, visibility(c) {
    u = c, w(), c && A();
  }, dispose() {
    i = !1, w(), n == null || n.abort();
  } };
}
const Te = ["data-task-id"], Ne = { class: "qs-card-header" }, Re = {
  key: 0,
  class: "widget-action-group"
}, Be = {
  key: 1,
  class: "qs-card-actions"
}, Fe = { class: "qs-card-menu" }, ze = ["aria-label"], De = { class: "fn-speed-stage" }, Ee = { class: "fn-speed-caption" }, Pe = { class: "qs-card-metrics" }, Ie = { class: "qs-card-time" }, Le = ["datetime"], Ve = { class: "qs-card-statuses" }, Ue = ["data-tone"], Oe = ["title"], Me = ["data-tone"], We = ["title"], $e = { class: "fn-lan-summary" }, je = {
  key: 0,
  class: "qs-card-progress",
  role: "status"
}, Je = ["disabled"], Ge = {
  key: 1,
  class: "qs-card-alert",
  role: "alert"
}, He = {
  key: 2,
  class: "qs-card-alert",
  role: "status"
}, Ke = {
  key: 3,
  class: "qs-card-note",
  role: "status"
}, Qe = {
  key: 4,
  class: "qs-card-alert",
  role: "status"
}, Xe = { class: "qs-card-footer" }, et = {
  __name: "Card",
  props: ["context"],
  setup(r) {
    const b = ve(() => import("./chunk.31ac0177.js")), y = ve({ loader: () => import("./chunk.ce51aa71.js"), timeout: 8e3, errorComponent: { render: () => j("p", { role: "alert", style: "padding:24px" }, [j("span", "FastNet 暂时无法打开 / Unable to open FastNet. "), j("a", { href: "/cgi-bin/luci/admin/services/fastnet/open", target: "_blank", rel: "noopener" }, "新窗口打开 / Open in new window ↗")]) } }), a = r, i = a.context, u = i.locale === "en" ? "en" : "zh-cn", e = (d, t) => u === "en" ? t : d, p = Se(i, we), n = p.state, q = "/cgi-bin/luci/admin/services/fastnet", g = R(() => Ae(n.summary)), w = R(() => _(n.task)), N = { preparing: e("准备测速", "Preparing"), ping: e("检测延迟", "Testing latency"), download: e("测试下载", "Testing download"), upload: e("测试上传", "Testing upload"), nat: e("检测 NAT", "Checking NAT"), ipv6: e("检测 IPv6", "Checking IPv6") }, S = R(() => {
      var d, t;
      return ((d = n.task) == null ? void 0 : d.state) === "cancel_requested" ? e("正在停止", "Stopping") : N[(t = n.task) == null ? void 0 : t.stage] || e("测速中", "Testing");
    }), V = R(() => n.error === "permission" ? e("登录已失效或权限不足，请重新登录", "Session expired or permission denied; sign in again") : n.error === "upgrade" ? e("插件接口不可用，请检查或升级 FastNet", "Plugin API unavailable; check or update FastNet") : n.paused ? e("连接连续失败，已暂停查询；后台任务继续运行", "Queries paused after repeated failures; the background task continues") : e("暂时无法确认结果，保留已有数据", "Result unavailable; existing data retained")), A = R(() => {
      var d;
      return { failed: e("本次测速失败，保留上次结果", "Test failed; previous results retained"), partial: e("部分检测未完成，已保留各项有效结果", "Some probes failed; valid results retained"), cancelled: e("已停止，保留上次结果", "Stopped; previous results retained"), interrupted: e("任务已中断，可重新测速", "Task interrupted; start a new test") }[(d = n.task) == null ? void 0 : d.state];
    }), U = R(() => [{ id: "details", label: e("查看上次结果", "Last result details") }, { id: "history", label: e("测速历史", "Test history") }, { id: "reload", label: e("重新读取", "Reload") }, { id: "settings", label: e("插件设置", "Plugin settings") }, { id: "full", label: e("完整 FastNet", "Full FastNet") }]);
    function O(d) {
      d === "details" ? X() : d === "history" ? T("history") : d === "reload" ? p.reload() : d === "settings" ? window.open(q, "_blank", "noopener") : d === "full" && T();
    }
    const c = J(!1), f = J(null), m = J(!1);
    let B, F, M = !0;
    function Q(d) {
      var v, x;
      const t = (x = (v = n.summary) == null ? void 0 : v.latest) == null ? void 0 : x[d];
      return W(d) || (t == null ? void 0 : t.status) === "error" ? "warning" : (t == null ? void 0 : t.status) === "ok" ? "good" : "neutral";
    }
    function T(d) {
      var v, x;
      const t = (v = d == null ? void 0 : d.currentTarget) == null ? void 0 : v.closest("details");
      t == null || t.removeAttribute("open"), (x = t == null ? void 0 : t.querySelector("summary")) == null || x.focus({ preventScroll: !0 }), c.value = !0, p.visibility(!1), i.openDetails(y, { context: i, locale: u, view: d === "history" ? "history" : "quick" }, { wide: !0, headerAction: { href: q + "/open", label: e("新窗口打开", "Open in new window") }, onClose() {
        c.value = !1, p.visibility(!document.hidden && !c.value && M);
      } });
    }
    const W = (d) => {
      var t, v, x;
      return !w.value && !!((x = (v = (t = n.summary) == null ? void 0 : t.lastTask) == null ? void 0 : v.issues) != null && x[d]);
    };
    function P(d) {
      var x, z;
      const t = (z = (x = n.summary) == null ? void 0 : x.latest) == null ? void 0 : z[d];
      let v;
      return !t || t.status === "not_tested" ? v = e("未检测", "Not tested") : t.status === "error" ? v = e("检测失败", "Probe failed") : t.status === "unavailable" ? v = e("不可用", "Unavailable") : d === "ipv6" ? v = /部分|准备度 [0-9]\/10/.test(t.value) ? e("部分可用", "Partly available") : e("可用", "Available") : v = /port.?restricted/i.test(t.value) ? e("端口受限锥形", "Port Restricted Cone") : /restricted.*cone/i.test(t.value) ? e("受限锥形", "Restricted Cone") : /full.?cone/i.test(t.value) ? e("全锥形", "Full Cone") : /symmetric/i.test(t.value) ? e("对称型", "Symmetric") : t.value, W(d) ? v + " · " + e("本次失败", "latest failed") : v;
    }
    function X(d) {
      var v, x;
      const t = (v = d == null ? void 0 : d.currentTarget) == null ? void 0 : v.closest("details");
      t == null || t.removeAttribute("open"), (x = t == null ? void 0 : t.querySelector("summary")) == null || x.focus({ preventScroll: !0 }), i.openDetails(b, { state: n, locale: u, stamp: H, mbps: E });
    }
    function I() {
      p.visibility(!document.hidden && !c.value && M);
    }
    return qe(() => {
      B = new ResizeObserver(() => {
        var d;
        m.value = ((d = f.value) == null ? void 0 : d.clientHeight) < 300;
      }), f.value && B.observe(f.value), F = new IntersectionObserver((d) => {
        var t;
        M = ((t = d[0]) == null ? void 0 : t.isIntersecting) !== !1, I();
      }), f.value && F.observe(f.value), document.addEventListener("visibilitychange", I), I();
    }), xe(() => {
      B == null || B.disconnect(), F == null || F.disconnect(), document.removeEventListener("visibilitychange", I), p.dispose();
    }), (d, t) => {
      var v, x, z, Y, Z, ee, te, ae, se, re, ne, ie, de, oe, le, ue, ce, pe, fe, me, ge;
      return k(), C("article", {
        ref_key: "root",
        ref: f,
        class: G(["qs-card-content", { "qs-card-summary": o(i).form === "summary", "fn-dense": m.value }]),
        "data-fastnet-card": "",
        "data-task-id": w.value ? o(n).task.id : void 0
      }, [
        s("header", Ne, [
          s("h2", null, [
            t[4] || (t[4] = s("svg", {
              viewBox: "0 0 24 24",
              "aria-hidden": "true"
            }, [
              s("path", { d: "M3 12h4l3-8 4 16 3-8h4" })
            ], -1)),
            h(l(e("外网测速", "Internet speed")), 1)
          ]),
          (v = o(i).components) != null && v.PrimaryAction && ((x = o(i).components) != null && x.Menu) ? (k(), C("div", Re, [
            (k(), ye(be(o(i).components.PrimaryAction), {
              icon: "activity",
              "data-fastnet-test": "",
              onClick: T
            }, {
              default: he(() => [
                h(l(w.value ? e("查看进度", "View progress") : e("测速", "Test")), 1)
              ]),
              _: 1
            })),
            (k(), ye(be(o(i).components.Menu), {
              label: e("外网测速更多操作", "Internet speed actions"),
              items: U.value,
              onSelect: O
            }, null, 40, ["label", "items"]))
          ])) : (k(), C("div", Be, [
            s("button", {
              class: "qs-card-primary",
              "data-fastnet-test": "",
              onClick: T
            }, l(w.value ? e("查看进度", "View progress") : e("测速", "Test")), 1),
            s("details", Fe, [
              s("summary", {
                "aria-label": e("外网测速更多操作", "Internet speed actions")
              }, "⋮", 8, ze),
              s("div", null, [
                s("button", {
                  "data-fastnet-details": "",
                  onClick: X
                }, l(e("查看上次结果", "Last result details")), 1),
                s("button", {
                  onClick: t[0] || (t[0] = ($) => T("history"))
                }, l(e("测速历史", "Test history")), 1),
                s("button", {
                  onClick: t[1] || (t[1] = ($) => o(p).reload())
                }, l(e("重新读取", "Reload")), 1),
                s("a", {
                  href: q,
                  target: "_blank",
                  rel: "noopener"
                }, l(e("插件设置", "Plugin settings")), 1),
                s("button", { onClick: T }, l(e("完整 FastNet", "Full FastNet")), 1)
              ])
            ])
          ]))
        ]),
        s("div", De, [
          s("div", Ee, [
            s("span", null, "WAN · " + l(e("最近有效结果", "LATEST VALID RESULTS")), 1),
            s("span", {
              class: G(["fn-live", { "is-active": w.value }])
            }, l(w.value ? S.value : (z = g.value) != null && z.measuredAt ? e("已保存", "Saved") : e("等待测速", "Ready to test")), 3)
          ]),
          s("div", Pe, [
            s("div", null, [
              s("span", null, "↓ " + l(e("上次下载", "Last download")), 1),
              s("strong", null, [
                h(l(o(E)((Y = g.value) == null ? void 0 : Y.downloadBps)), 1),
                t[5] || (t[5] = s("small", null, "Mbps", -1))
              ])
            ]),
            s("div", null, [
              s("span", null, "↑ " + l(e("上次上传", "Last upload")), 1),
              s("strong", null, [
                h(l(o(E)((Z = g.value) == null ? void 0 : Z.uploadBps)), 1),
                t[6] || (t[6] = s("small", null, "Mbps", -1))
              ])
            ])
          ]),
          s("p", Ie, [
            h(l(e("上次测速", "Last tested")) + " ", 1),
            s("time", {
              datetime: ((ee = g.value) == null ? void 0 : ee.measuredAt) || void 0
            }, l((te = g.value) != null && te.measuredAt ? o(H)(g.value.measuredAt, o(u)) : e("尚未测速", "No test yet")), 9, Le)
          ])
        ]),
        s("div", Ve, [
          s("div", {
            "data-tone": Q("nat")
          }, [
            t[7] || (t[7] = s("span", null, [
              s("i", { "aria-hidden": "true" }),
              h("NAT")
            ], -1)),
            s("strong", {
              title: P("nat")
            }, l(P("nat")), 9, Oe)
          ], 8, Ue),
          s("div", {
            "data-tone": Q("ipv6")
          }, [
            t[8] || (t[8] = s("span", null, [
              s("i", { "aria-hidden": "true" }),
              h("IPv6")
            ], -1)),
            s("strong", {
              class: G({ "qs-card-warning": W("ipv6") }),
              title: P("ipv6")
            }, l(P("ipv6")), 11, We)
          ], 8, Me)
        ]),
        s("div", $e, [
          s("span", null, "LAN · " + l(e("浏览器 → 路由器", "Browser → Router")), 1),
          s("strong", null, [
            h("↓ " + l(o(E)((re = (se = (ae = o(n).summary) == null ? void 0 : ae.latestResults) == null ? void 0 : se.lanDownload) == null ? void 0 : re.value)) + " · ↑ " + l(o(E)((de = (ie = (ne = o(n).summary) == null ? void 0 : ne.latestResults) == null ? void 0 : ie.lanUpload) == null ? void 0 : de.value)) + " ", 1),
            t[9] || (t[9] = s("small", null, "Mbps", -1))
          ]),
          s("time", null, l(o(H)([(ue = (le = (oe = o(n).summary) == null ? void 0 : oe.latestResults) == null ? void 0 : le.lanDownload) == null ? void 0 : ue.measuredAt, (fe = (pe = (ce = o(n).summary) == null ? void 0 : ce.latestResults) == null ? void 0 : pe.lanUpload) == null ? void 0 : fe.measuredAt].filter(Boolean).sort().pop(), o(u))), 1)
        ]),
        w.value ? (k(), C("div", je, [
          s("span", null, [
            h(l(S.value), 1),
            s("small", null, l(e("上次有效结果保持显示", "Previous valid results remain visible")), 1)
          ]),
          s("button", {
            disabled: o(n).cancelling || o(n).task.state === "cancel_requested",
            onClick: t[2] || (t[2] = ($) => o(p).stop())
          }, l(o(n).cancelling || o(n).task.state === "cancel_requested" ? e("正在停止", "Stopping") : e("停止", "Stop")), 9, Je)
        ])) : L("", !0),
        o(n).error ? (k(), C("p", Ge, [
          h(l(V.value) + " ", 1),
          s("button", {
            onClick: t[3] || (t[3] = ($) => o(n).errorAction === "run" ? T() : o(p).reload())
          }, l(o(n).paused ? e("恢复查询", "Resume queries") : e("重试", "Retry")), 1)
        ])) : o(n).summary && o(n).summary.service.state !== "ready" ? (k(), C("p", He, [
          h(l(o(n).summary.service.state === "disabled" ? e("服务未启用", "Service disabled") : e("服务暂不可用", "Service unavailable")) + " ", 1),
          s("a", { href: q }, l(e("打开设置", "Open settings")), 1)
        ])) : o(n).task && ["failed", "cancelled", "interrupted", "partial"].includes(o(n).task.state) ? (k(), C("p", Ke, [
          h(l(A.value) + " ", 1),
          o(n).task.state === "failed" ? (k(), C("button", {
            key: 0,
            onClick: T
          }, l(e("重试测速", "Retry test")), 1)) : L("", !0)
        ])) : L("", !0),
        (me = o(n).summary) != null && me.service.persistenceError ? (k(), C("p", Qe, l(e("结果保存失败，请检查设备存储", "Result could not be saved; check device storage")), 1)) : L("", !0),
        s("footer", Xe, [
          s("span", null, [
            t[10] || (t[10] = s("span", {
              class: "fn-route-dot",
              "aria-hidden": "true"
            }, null, -1)),
            h(l(o(Ce)((ge = g.value) == null ? void 0 : ge.measuredAt) ? e("结果较早，可重新测速", "Older result; test again") : e("默认外网出口", "Default WAN route")), 1)
          ]),
          t[11] || (t[11] = s("small", null, [
            h("FASTNET "),
            s("span", { "aria-hidden": "true" }, "↗")
          ], -1))
        ])
      ], 10, Te);
    };
  }
};
if (!document.getElementById("fastnet-card-v1-style")) {
  const r = document.createElement("style");
  r.id = "fastnet-card-v1-style", r.textContent = ke, document.head.appendChild(r);
}
const tt = 1;
export {
  tt as apiVersion,
  et as default
};
