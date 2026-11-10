var P = (s, b, v) => new Promise((t, i) => {
  var o = (n) => {
    try {
      m(v.next(n));
    } catch (q) {
      i(q);
    }
  }, e = (n) => {
    try {
      m(v.throw(n));
    } catch (q) {
      i(q);
    }
  }, m = (n) => n.done ? t(n.value) : Promise.resolve(n.value).then(o, e);
  m((v = v.apply(s, b)).next());
});
import { defineAsyncComponent as pe, h as $, computed as z, ref as j, onMounted as ve, onUnmounted as ye, openBlock as C, createElementBlock as B, unref as l, normalizeClass as W, createElementVNode as r, createTextVNode as w, toDisplayString as c, createBlock as me, resolveDynamicComponent as fe, withCtx as be, createCommentVNode as ge, reactive as qe } from "/luci-static/quickstart/card-runtime-v1.js";
const xe = '[data-fastnet-card]{--fn-down:var(--qs-card-accent);position:relative;isolation:isolate;gap:14px;background:linear-gradient(145deg,transparent 48%,#7b9ee909);border-radius:inherit}[data-fastnet-card] .qs-card-header h2>svg{color:var(--fn-down)}[data-fastnet-card] .qs-card-primary{background:var(--qs-card-accent);color:var(--qs-card-panel);border-color:transparent;padding:6px 13px;border-radius:9px;font-weight:600}[data-fastnet-card] .qs-card-menu>summary{border-color:transparent;color:var(--qs-card-muted)}[data-fastnet-card] .fn-speed-stage{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:center;gap:14px;padding:18px 20px;border-radius:14px;border:1px solid var(--qs-card-line);background:linear-gradient(120deg,#608ee90c,transparent 75%),var(--qs-card-soft)}[data-fastnet-card] .fn-speed-caption{display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:10px;letter-spacing:.7px;color:var(--qs-card-muted)}[data-fastnet-card] .fn-live{display:flex;align-items:center;gap:5px;letter-spacing:0;white-space:nowrap}[data-fastnet-card] .fn-live:before{content:"";width:5px;height:5px;border-radius:50%;background:var(--qs-card-muted)}[data-fastnet-card] .fn-live.is-active{color:var(--qs-card-accent)}[data-fastnet-card] .fn-live.is-active:before{background:currentColor;box-shadow:0 0 0 3px #6794ef20}[data-fastnet-card] .qs-card-metrics{gap:18px;align-items:center;grid-template-columns:1.25fr 1fr}[data-fastnet-card] .qs-card-metrics strong{font-size:clamp(30px,3.5vw,52px);line-height:1.15;letter-spacing:-1.7px;font-weight:700;margin-top:4px;color:var(--fn-down)}[data-fastnet-card] .qs-card-metrics>div+div{border-left:1px solid var(--qs-card-line);padding-left:18px}[data-fastnet-card] .qs-card-metrics>div+div strong{font-size:clamp(25px,2.5vw,36px);color:var(--qs-card-text);letter-spacing:-.9px}[data-fastnet-card] .qs-card-metrics small{letter-spacing:0}[data-fastnet-card] .qs-card-time{gap:5px;font-size:10px}[data-fastnet-card] .qs-card-statuses{padding:0;border:0;gap:10px}[data-fastnet-card] .qs-card-statuses>div{padding:10px 12px;border:1px solid var(--qs-card-line);border-radius:10px;background:var(--qs-card-panel)}[data-fastnet-card] .qs-card-statuses span{display:flex;align-items:center;gap:6px;letter-spacing:.3px;margin-bottom:3px}[data-fastnet-card] .qs-card-statuses i{width:6px;height:6px;border-radius:50%;background:var(--qs-card-muted)}[data-fastnet-card] .qs-card-statuses [data-tone=good] i{background:var(--qs-card-good)}[data-fastnet-card] .qs-card-statuses [data-tone=warning] i{background:var(--qs-card-warning)}[data-fastnet-card].qs-card-summary{gap:3px;background:none}[data-fastnet-card].qs-card-summary .fn-speed-stage{display:block;flex:none;padding:0;border:0;background:none}[data-fastnet-card].qs-card-summary .fn-speed-caption{display:none}[data-fastnet-card].qs-card-summary .qs-card-metrics{grid-template-columns:1fr 1fr;gap:12px}[data-fastnet-card].qs-card-summary .qs-card-metrics strong{font-size:23px;letter-spacing:-.5px;margin:0}[data-fastnet-card].qs-card-summary .qs-card-metrics>div+div{padding:0;border:0}[data-fastnet-card].qs-card-summary .qs-card-statuses>div{padding:0;border:0;background:none;max-width:50%}[data-fastnet-card].qs-card-summary .qs-card-statuses span{margin:0;gap:4px}[data-fastnet-card].qs-card-summary .qs-card-statuses i{width:4px;height:4px}[data-fastnet-card].qs-card-summary .qs-card-primary{padding:2px 7px;border-radius:6px}@media(max-width:600px){[data-fastnet-card]:not(.qs-card-summary) .fn-speed-stage{padding:14px;gap:12px}[data-fastnet-card]:not(.qs-card-summary) .qs-card-metrics strong{font-size:36px}[data-fastnet-card]:not(.qs-card-summary) .qs-card-metrics>div+div strong{font-size:28px}}[data-fastnet-card].fn-dense:not(.qs-card-summary){gap:6px;padding:12px 16px}[data-fastnet-card].fn-dense:not(.qs-card-summary) .fn-speed-stage{padding:10px 12px;gap:6px}[data-fastnet-card].fn-dense:not(.qs-card-summary) .fn-speed-caption{display:none}[data-fastnet-card].fn-dense:not(.qs-card-summary) .qs-card-metrics strong{font-size:32px;line-height:1.15;margin:0}[data-fastnet-card].fn-dense:not(.qs-card-summary) .qs-card-metrics>div+div strong{font-size:27px}[data-fastnet-card].fn-dense:not(.qs-card-summary) .qs-card-statuses>div{padding:6px 9px}.fn-lan-summary{display:grid;grid-template-columns:1fr auto;gap:3px 8px;font-size:10px;color:var(--qs-card-muted);border-top:1px solid var(--qs-card-line);padding-top:8px}.fn-lan-summary strong{font-size:12px;font-weight:500;color:var(--qs-card-text);white-space:nowrap}.fn-lan-summary small{font-size:9px;font-weight:400}.fn-lan-summary time{grid-column:1/-1;font-size:10px}.qs-card-summary .fn-lan-summary{padding-top:2px;border:0;gap:1px}.qs-card-summary .fn-lan-summary time{display:none}', k = (s) => s && ["running", "cancel_requested"].includes(s.state), G = ["running", "cancel_requested", "succeeded", "partial", "failed", "cancelled", "interrupted"];
function he(s) {
  var b, v, t, i;
  if ((s == null ? void 0 : s.schemaVersion) !== 1 || !["ready", "disabled", "unavailable"].includes((b = s.service) == null ? void 0 : b.state) || !("latest" in s) || !("task" in s)) throw Error("invalid_summary");
  if ((v = s.latest) != null && v.bandwidth) {
    const o = s.latest.bandwidth;
    if (![o.downloadBps, o.uploadBps].every((e) => typeof e == "number" && Number.isFinite(e) && e >= 0) || !o.measuredAt || !Number.isFinite(Date.parse(o.measuredAt))) throw Error("invalid_bandwidth");
  }
  if (s.task && !G.includes(s.task.state)) throw Error("invalid_task");
  for (const o of ["download", "upload", "nat", "ipv6"]) if (s.latest) {
    const e = s.latest[o];
    if (!e || !["ok", "unavailable", "error", "not_tested"].includes(e.status) || e.value !== null && (["download", "upload"].includes(o) ? typeof e.value != "number" || !Number.isFinite(e.value) || e.value < 0 : typeof e.value != "string")) throw Error("invalid_measurement");
  }
  for (const o of ["download", "upload", "lanDownload", "lanUpload", "lanPing"]) {
    const e = (i = (t = s.latestResults) == null ? void 0 : t[o]) == null ? void 0 : i.value;
    if (e != null && (!Number.isFinite(e) || e < 0)) throw Error("invalid_measurement");
  }
  return s;
}
function we(s) {
  var t, i;
  const b = s == null ? void 0 : s.latestResults;
  if (b != null && b.download || b != null && b.upload) {
    const o = b.download, e = b.upload;
    return { downloadBps: (t = o == null ? void 0 : o.value) != null ? t : null, uploadBps: (i = e == null ? void 0 : e.value) != null ? i : null, measuredAt: [o == null ? void 0 : o.measuredAt, e == null ? void 0 : e.measuredAt].filter(Boolean).sort().pop(), mixed: !!(o && e && o.runId !== e.runId) };
  }
  const v = s == null ? void 0 : s.latest;
  return v ? v.bandwidth || { downloadBps: v.download.status === "ok" ? v.download.value : null, uploadBps: v.upload.status === "ok" ? v.upload.value : null, measuredAt: v.measuredAt } : null;
}
function E(s) {
  return s == null ? "—" : s > 0 && s < 1e5 ? "<0.1" : (s / 1e6).toLocaleString("en-US", { maximumFractionDigits: s >= 1e8 ? 0 : 1 });
}
function J(s, b) {
  return !s || !Number.isFinite(Date.parse(s)) ? "—" : new Date(s).toLocaleString(b === "en" ? "en-GB" : "zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: !1 });
}
function ke(s, b = (t) => t, v = globalThis) {
  const t = b({ loading: !1, summary: null, task: null, submitting: !1, cancelling: !1, error: "", errorAction: "read", paused: !1, failures: 0 });
  let i = !0, o = !0, e, m, n, q = null, f = 0;
  const h = () => {
    v.clearTimeout(e), e = void 0, m == null || m.abort(), m = void 0, f++;
  }, N = (u) => [401, 403].includes(u == null ? void 0 : u.status) ? "permission" : (u == null ? void 0 : u.status) === 404 ? "upgrade" : "unavailable", A = () => {
    i && o && !t.paused && (e = v.setTimeout(k(t.task) ? L : _, k(t.task) ? 2e3 : 15e3));
  };
  function L() {
    return P(this, null, function* () {
      if (!i || !o || !k(t.task)) return;
      const u = t.task.id, y = ++f;
      m = new AbortController();
      try {
        const p = yield s.request("/task?id=" + encodeURIComponent(u), { signal: m.signal });
        if (!i || y !== f) return;
        if (p.id !== u || !G.includes(p.state)) throw Error("invalid_task");
        if (t.task = p, t.failures = 0, t.error = "", !k(p)) {
          q = null, yield _();
          return;
        }
      } catch (p) {
        if (!i || y !== f) return;
        t.failures++, t.error = N(p), t.errorAction = "read", (t.failures >= 3 || ["permission", "upgrade"].includes(t.error)) && (t.paused = !0);
      } finally {
        i && y === f && (m = void 0, A());
      }
    });
  }
  function _() {
    return P(this, null, function* () {
      if (h(), !i || !o) return;
      const u = f;
      t.loading = !0, m = new AbortController();
      try {
        const y = he(yield s.request("/summary", { signal: m.signal }));
        if (!i || u !== f) return;
        t.summary = y, t.task = y.task || y.lastTask || null, t.error = "", t.failures = 0, t.paused = !1, k(t.task) && (q = null);
      } catch (y) {
        i && u === f && (t.error = N(y), t.errorAction = "read", t.failures++, t.paused = t.failures >= 3 || ["permission", "upgrade"].includes(t.error));
      } finally {
        i && u === f && (t.loading = !1, m = void 0, A());
      }
    });
  }
  function V() {
    return P(this, null, function* () {
      var y;
      if (!i || t.error === "permission" || t.submitting || k(t.task) || t.loading || ((y = t.summary) == null ? void 0 : y.service.state) !== "ready") return;
      h();
      const u = f;
      t.submitting = !0, t.error = "", n = new AbortController(), q || (q = Array.from(crypto.getRandomValues(new Uint8Array(16)), (p) => p.toString(16).padStart(2, "0")).join(""));
      try {
        const p = yield s.request("/run", { method: "POST", body: JSON.stringify({ idempotencyKey: q }), signal: n.signal });
        if (!i) return;
        if (!G.includes(p.state)) throw Error("invalid_task");
        if (q = null, u !== f) return;
        t.task = p, t.paused = !1, t.failures = 0, k(p) ? A() : yield _();
      } catch (p) {
        if (!i || u !== f) return;
        (p == null ? void 0 : p.status) === 409 ? (q = null, yield _()) : (t.error = N(p), t.errorAction = ["permission", "upgrade"].includes(t.error) ? "read" : "run", p != null && p.status && p.status < 500 && (q = null));
      } finally {
        i && (t.submitting = !1, n = void 0);
      }
    });
  }
  function T() {
    return P(this, null, function* () {
      if (!i || !k(t.task) || t.cancelling) return;
      h();
      const u = f;
      t.cancelling = !0, n = new AbortController();
      try {
        const y = yield s.request("/cancel", { method: "POST", body: JSON.stringify({ id: t.task.id }), signal: n.signal });
        if (!i || u !== f) return;
        t.task = y, k(y) ? A() : yield _();
      } catch (y) {
        i && u === f && (t.error = N(y), t.errorAction = "read", A());
      } finally {
        i && (t.cancelling = !1, n = void 0);
      }
    });
  }
  return { state: t, start: V, stop: T, reload: _, visibility(u) {
    o = u, h(), u && _();
  }, dispose() {
    i = !1, h(), n == null || n.abort();
  } };
}
const _e = ["data-task-id"], Ae = { class: "qs-card-header" }, Ce = {
  key: 0,
  class: "widget-action-group"
}, Se = {
  key: 1,
  class: "qs-card-actions"
}, Ne = { class: "qs-card-menu" }, Te = ["aria-label"], Be = { class: "fn-speed-stage" }, Re = { class: "fn-speed-caption" }, Fe = { class: "qs-card-metrics" }, Pe = { class: "qs-card-time" }, ze = ["datetime"], Ee = { class: "qs-card-statuses" }, Ie = ["data-tone"], De = ["title"], Le = ["data-tone"], Ve = ["title"], Ue = { class: "fn-lan-summary" }, Me = {
  key: 0,
  class: "qs-card-progress",
  role: "status"
}, Oe = ["disabled"], $e = {
  key: 1,
  class: "qs-card-alert",
  role: "alert"
}, je = {
  key: 2,
  class: "qs-card-alert",
  role: "status"
}, Ge = {
  __name: "Card",
  props: ["context"],
  setup(s) {
    const b = pe(() => import("./chunk.31ac0177.js")), v = pe({ loader: () => import("./chunk.ce51aa71.js"), timeout: 8e3, errorComponent: { render: () => $("p", { role: "alert", style: "padding:24px" }, [$("span", "FastNet 暂时无法打开 / Unable to open FastNet. "), $("a", { href: "/cgi-bin/luci/admin/services/fastnet/open", target: "_blank", rel: "noopener" }, "新窗口打开 / Open in new window ↗")]) } }), t = s, i = t.context, o = i.locale === "en" ? "en" : "zh-cn", e = (d, a) => o === "en" ? a : d, m = ke(i, qe), n = m.state, q = "/cgi-bin/luci/admin/services/fastnet", f = z(() => we(n.summary)), h = z(() => k(n.task)), N = { preparing: e("准备测速", "Preparing"), ping: e("检测延迟", "Testing latency"), download: e("测试下载", "Testing download"), upload: e("测试上传", "Testing upload"), nat: e("检测 NAT", "Checking NAT"), ipv6: e("检测 IPv6", "Checking IPv6") }, A = z(() => {
      var d, a;
      return ((d = n.task) == null ? void 0 : d.state) === "cancel_requested" ? e("正在停止", "Stopping") : N[(a = n.task) == null ? void 0 : a.stage] || e("测速中", "Testing");
    }), L = z(() => n.error === "permission" ? e("登录已失效或权限不足，请重新登录", "Session expired or permission denied; sign in again") : n.error === "upgrade" ? e("插件接口不可用，请检查或升级 FastNet", "Plugin API unavailable; check or update FastNet") : n.paused ? e("连接连续失败，已暂停查询；后台任务继续运行", "Queries paused after repeated failures; the background task continues") : e("暂时无法确认结果，保留已有数据", "Result unavailable; existing data retained")), _ = z(() => [{ id: "details", label: e("查看上次结果", "Last result details") }, { id: "history", label: e("测速历史", "Test history") }, { id: "reload", label: e("重新读取", "Reload") }, { id: "settings", label: e("插件设置", "Plugin settings") }, { id: "full", label: e("完整 FastNet", "Full FastNet") }]);
    function V(d) {
      d === "details" ? K() : d === "history" ? S("history") : d === "reload" ? m.reload() : d === "settings" ? window.open(q, "_blank", "noopener") : d === "full" && S();
    }
    const T = j(!1), u = j(null), y = j(!1);
    let p, R, U = !0;
    function H(d) {
      var g, x;
      const a = (x = (g = n.summary) == null ? void 0 : g.latest) == null ? void 0 : x[d];
      return M(d) || (a == null ? void 0 : a.status) === "error" ? "warning" : (a == null ? void 0 : a.status) === "ok" ? "good" : "neutral";
    }
    function S(d) {
      var g, x;
      const a = (g = d == null ? void 0 : d.currentTarget) == null ? void 0 : g.closest("details");
      a == null || a.removeAttribute("open"), (x = a == null ? void 0 : a.querySelector("summary")) == null || x.focus({ preventScroll: !0 }), T.value = !0, m.visibility(!1), i.openDetails(v, { context: i, locale: o, view: d === "history" ? "history" : "quick" }, { wide: !0, headerAction: { href: q + "/open", label: e("新窗口打开", "Open in new window") }, onClose() {
        T.value = !1, m.visibility(!document.hidden && !T.value && U);
      } });
    }
    const M = (d) => {
      var a, g, x;
      return !h.value && !!((x = (g = (a = n.summary) == null ? void 0 : a.lastTask) == null ? void 0 : g.issues) != null && x[d]);
    };
    function I(d) {
      var x, F;
      const a = (F = (x = n.summary) == null ? void 0 : x.latest) == null ? void 0 : F[d];
      let g;
      return !a || a.status === "not_tested" ? g = e("未检测", "Not tested") : a.status === "error" ? g = e("检测失败", "Probe failed") : a.status === "unavailable" ? g = e("不可用", "Unavailable") : d === "ipv6" ? g = /部分|准备度 [0-9]\/10/.test(a.value) ? e("部分可用", "Partly available") : e("可用", "Available") : g = /port.?restricted/i.test(a.value) ? e("端口受限锥形", "Port Restricted Cone") : /restricted.*cone/i.test(a.value) ? e("受限锥形", "Restricted Cone") : /full.?cone/i.test(a.value) ? e("全锥形", "Full Cone") : /symmetric/i.test(a.value) ? e("对称型", "Symmetric") : a.value, M(d) ? g + " · " + e("本次失败", "latest failed") : g;
    }
    function K(d) {
      var g, x;
      const a = (g = d == null ? void 0 : d.currentTarget) == null ? void 0 : g.closest("details");
      a == null || a.removeAttribute("open"), (x = a == null ? void 0 : a.querySelector("summary")) == null || x.focus({ preventScroll: !0 }), i.openDetails(b, { state: n, locale: o, stamp: J, mbps: E });
    }
    function D() {
      m.visibility(!document.hidden && !T.value && U);
    }
    return ve(() => {
      p = new ResizeObserver(() => {
        var d;
        y.value = ((d = u.value) == null ? void 0 : d.clientHeight) < 300;
      }), u.value && p.observe(u.value), R = new IntersectionObserver((d) => {
        var a;
        U = ((a = d[0]) == null ? void 0 : a.isIntersecting) !== !1, D();
      }), u.value && R.observe(u.value), document.addEventListener("visibilitychange", D), D();
    }), ye(() => {
      p == null || p.disconnect(), R == null || R.disconnect(), document.removeEventListener("visibilitychange", D), m.dispose();
    }), (d, a) => {
      var g, x, F, Q, X, Y, Z, ee, te, ae, se, re, ne, ie, de, oe, le, ue, ce;
      return C(), B("article", {
        ref_key: "root",
        ref: u,
        class: W(["qs-card-content", { "qs-card-summary": l(i).form === "summary", "fn-dense": y.value }]),
        "data-fastnet-card": "",
        "data-task-id": h.value ? l(n).task.id : void 0
      }, [
        r("header", Ae, [
          r("h2", null, [
            a[4] || (a[4] = r("svg", {
              viewBox: "0 0 24 24",
              "aria-hidden": "true"
            }, [
              r("path", { d: "M3 12h4l3-8 4 16 3-8h4" })
            ], -1)),
            w(c(e("外网测速", "Internet speed")), 1)
          ]),
          (g = l(i).components) != null && g.PrimaryAction && ((x = l(i).components) != null && x.Menu) ? (C(), B("div", Ce, [
            (C(), me(fe(l(i).components.PrimaryAction), {
              icon: "activity",
              "data-fastnet-test": "",
              onClick: S
            }, {
              default: be(() => [
                w(c(h.value ? e("查看进度", "View progress") : e("测速", "Test")), 1)
              ]),
              _: 1
            })),
            (C(), me(fe(l(i).components.Menu), {
              label: e("外网测速更多操作", "Internet speed actions"),
              items: _.value,
              onSelect: V
            }, null, 40, ["label", "items"]))
          ])) : (C(), B("div", Se, [
            r("button", {
              class: "qs-card-primary",
              "data-fastnet-test": "",
              onClick: S
            }, c(h.value ? e("查看进度", "View progress") : e("测速", "Test")), 1),
            r("details", Ne, [
              r("summary", {
                "aria-label": e("外网测速更多操作", "Internet speed actions")
              }, "⋮", 8, Te),
              r("div", null, [
                r("button", {
                  "data-fastnet-details": "",
                  onClick: K
                }, c(e("查看上次结果", "Last result details")), 1),
                r("button", {
                  onClick: a[0] || (a[0] = (O) => S("history"))
                }, c(e("测速历史", "Test history")), 1),
                r("button", {
                  onClick: a[1] || (a[1] = (O) => l(m).reload())
                }, c(e("重新读取", "Reload")), 1),
                r("a", {
                  href: q,
                  target: "_blank",
                  rel: "noopener"
                }, c(e("插件设置", "Plugin settings")), 1),
                r("button", { onClick: S }, c(e("完整 FastNet", "Full FastNet")), 1)
              ])
            ])
          ]))
        ]),
        r("div", Be, [
          r("div", Re, [
            r("span", null, "WAN · " + c(e("最近有效结果", "LATEST VALID RESULTS")), 1),
            r("span", {
              class: W(["fn-live", { "is-active": h.value }])
            }, c(h.value ? A.value : (F = f.value) != null && F.measuredAt ? e("已保存", "Saved") : e("等待测速", "Ready to test")), 3)
          ]),
          r("div", Fe, [
            r("div", null, [
              r("span", null, "↓ " + c(e("上次下载", "Last download")), 1),
              r("strong", null, [
                w(c(l(E)((Q = f.value) == null ? void 0 : Q.downloadBps)), 1),
                a[5] || (a[5] = r("small", null, "Mbps", -1))
              ])
            ]),
            r("div", null, [
              r("span", null, "↑ " + c(e("上次上传", "Last upload")), 1),
              r("strong", null, [
                w(c(l(E)((X = f.value) == null ? void 0 : X.uploadBps)), 1),
                a[6] || (a[6] = r("small", null, "Mbps", -1))
              ])
            ])
          ]),
          r("p", Pe, [
            w(c(e("上次测速", "Last tested")) + " ", 1),
            r("time", {
              datetime: ((Y = f.value) == null ? void 0 : Y.measuredAt) || void 0
            }, c((Z = f.value) != null && Z.measuredAt ? l(J)(f.value.measuredAt, l(o)) : e("尚未测速", "No test yet")), 9, ze)
          ])
        ]),
        r("div", Ee, [
          r("div", {
            "data-tone": H("nat")
          }, [
            a[7] || (a[7] = r("span", null, [
              r("i", { "aria-hidden": "true" }),
              w("NAT")
            ], -1)),
            r("strong", {
              title: I("nat")
            }, c(I("nat")), 9, De)
          ], 8, Ie),
          r("div", {
            "data-tone": H("ipv6")
          }, [
            a[8] || (a[8] = r("span", null, [
              r("i", { "aria-hidden": "true" }),
              w("IPv6")
            ], -1)),
            r("strong", {
              class: W({ "qs-card-warning": M("ipv6") }),
              title: I("ipv6")
            }, c(I("ipv6")), 11, Ve)
          ], 8, Le)
        ]),
        r("div", Ue, [
          r("span", null, "LAN · " + c(e("浏览器 → 路由器", "Browser → Router")), 1),
          r("strong", null, [
            w("↓ " + c(l(E)((ae = (te = (ee = l(n).summary) == null ? void 0 : ee.latestResults) == null ? void 0 : te.lanDownload) == null ? void 0 : ae.value)) + " · ↑ " + c(l(E)((ne = (re = (se = l(n).summary) == null ? void 0 : se.latestResults) == null ? void 0 : re.lanUpload) == null ? void 0 : ne.value)) + " ", 1),
            a[9] || (a[9] = r("small", null, "Mbps", -1))
          ]),
          r("time", null, c(l(J)([(oe = (de = (ie = l(n).summary) == null ? void 0 : ie.latestResults) == null ? void 0 : de.lanDownload) == null ? void 0 : oe.measuredAt, (ce = (ue = (le = l(n).summary) == null ? void 0 : le.latestResults) == null ? void 0 : ue.lanUpload) == null ? void 0 : ce.measuredAt].filter(Boolean).sort().pop(), l(o))), 1)
        ]),
        h.value ? (C(), B("div", Me, [
          r("span", null, [
            w(c(A.value), 1),
            r("small", null, c(e("上次有效结果保持显示", "Previous valid results remain visible")), 1)
          ]),
          r("button", {
            disabled: l(n).cancelling || l(n).task.state === "cancel_requested",
            onClick: a[2] || (a[2] = (O) => l(m).stop())
          }, c(l(n).cancelling || l(n).task.state === "cancel_requested" ? e("正在停止", "Stopping") : e("停止", "Stop")), 9, Oe)
        ])) : ge("", !0),
        l(n).error ? (C(), B("p", $e, [
          w(c(L.value) + " ", 1),
          r("button", {
            onClick: a[3] || (a[3] = (O) => l(n).errorAction === "run" ? S() : l(m).reload())
          }, c(l(n).paused ? e("恢复查询", "Resume queries") : e("重试", "Retry")), 1)
        ])) : l(n).summary && l(n).summary.service.state !== "ready" ? (C(), B("p", je, [
          w(c(l(n).summary.service.state === "disabled" ? e("服务未启用", "Service disabled") : e("服务暂不可用", "Service unavailable")) + " ", 1),
          r("a", { href: q }, c(e("打开设置", "Open settings")), 1)
        ])) : ge("", !0)
      ], 10, _e);
    };
  }
};
if (!document.getElementById("fastnet-card-v1-style")) {
  const s = document.createElement("style");
  s.id = "fastnet-card-v1-style", s.textContent = xe, document.head.appendChild(s);
}
const He = 1;
export {
  He as apiVersion,
  Ge as default
};
