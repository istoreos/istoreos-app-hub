var z = (r, v, h) => new Promise((e, i) => {
  var t = (l) => {
    try {
      n(h.next(l));
    } catch (f) {
      i(f);
    }
  }, b = (l) => {
    try {
      n(h.throw(l));
    } catch (f) {
      i(f);
    }
  }, n = (l) => l.done ? e(l.value) : Promise.resolve(l.value).then(t, b);
  n((h = h.apply(r, v)).next());
});
import { openBlock as x, createElementBlock as w, createElementVNode as s, toDisplayString as d, Fragment as ee, renderList as re, createTextVNode as k, unref as c, createCommentVNode as B, defineAsyncComponent as ne, h as V, computed as E, ref as M, onMounted as ie, onUnmounted as de, normalizeClass as U, createBlock as te, resolveDynamicComponent as ae, withCtx as oe, reactive as le } from "/luci-static/quickstart/card-runtime-v1.js";
const ce = '[data-fastnet-card]{--fn-down:var(--qs-card-accent);position:relative;isolation:isolate;gap:14px;background:linear-gradient(145deg,transparent 48%,#7b9ee909);border-radius:inherit}[data-fastnet-card] .qs-card-header h2>svg{color:var(--fn-down)}[data-fastnet-card] .qs-card-primary{background:var(--qs-card-accent);color:var(--qs-card-panel);border-color:transparent;padding:6px 13px;border-radius:9px;font-weight:600}[data-fastnet-card] .qs-card-menu>summary{border-color:transparent;color:var(--qs-card-muted)}[data-fastnet-card] .fn-speed-stage{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:center;gap:14px;padding:18px 20px;border-radius:14px;border:1px solid var(--qs-card-line);background:linear-gradient(120deg,#608ee90c,transparent 75%),var(--qs-card-soft)}[data-fastnet-card] .fn-speed-caption{display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:10px;letter-spacing:.7px;color:var(--qs-card-muted)}[data-fastnet-card] .fn-live{display:flex;align-items:center;gap:5px;letter-spacing:0;white-space:nowrap}[data-fastnet-card] .fn-live:before{content:"";width:5px;height:5px;border-radius:50%;background:var(--qs-card-muted)}[data-fastnet-card] .fn-live.is-active{color:var(--qs-card-accent)}[data-fastnet-card] .fn-live.is-active:before{background:currentColor;box-shadow:0 0 0 3px #6794ef20}[data-fastnet-card] .qs-card-metrics{gap:18px;align-items:center;grid-template-columns:1.25fr 1fr}[data-fastnet-card] .qs-card-metrics strong{font-size:clamp(30px,3.5vw,52px);line-height:1.15;letter-spacing:-1.7px;font-weight:700;margin-top:4px;color:var(--fn-down)}[data-fastnet-card] .qs-card-metrics>div+div{border-left:1px solid var(--qs-card-line);padding-left:18px}[data-fastnet-card] .qs-card-metrics>div+div strong{font-size:clamp(25px,2.5vw,36px);color:var(--qs-card-text);letter-spacing:-.9px}[data-fastnet-card] .qs-card-metrics small{letter-spacing:0}[data-fastnet-card] .qs-card-time{gap:5px;font-size:10px}[data-fastnet-card] .qs-card-statuses{padding:0;border:0;gap:10px}[data-fastnet-card] .qs-card-statuses>div{padding:10px 12px;border:1px solid var(--qs-card-line);border-radius:10px;background:var(--qs-card-panel)}[data-fastnet-card] .qs-card-statuses span{display:flex;align-items:center;gap:6px;letter-spacing:.3px;margin-bottom:3px}[data-fastnet-card] .qs-card-statuses i{width:6px;height:6px;border-radius:50%;background:var(--qs-card-muted)}[data-fastnet-card] .qs-card-statuses [data-tone=good] i{background:var(--qs-card-good)}[data-fastnet-card] .qs-card-statuses [data-tone=warning] i{background:var(--qs-card-warning)}[data-fastnet-card] .qs-card-footer{margin-top:0;align-items:center;font-size:10px}[data-fastnet-card] .qs-card-footer>span{display:flex;align-items:center;gap:6px}[data-fastnet-card] .fn-route-dot{width:5px;height:5px;border:1px solid var(--qs-card-muted);border-radius:50%}[data-fastnet-card] .qs-card-footer small{letter-spacing:1.5px;font-size:9px}[data-fastnet-card].qs-card-summary{gap:3px;background:none}[data-fastnet-card].qs-card-summary .fn-speed-stage{display:block;flex:none;padding:0;border:0;background:none}[data-fastnet-card].qs-card-summary .fn-speed-caption{display:none}[data-fastnet-card].qs-card-summary .qs-card-metrics{grid-template-columns:1fr 1fr;gap:12px}[data-fastnet-card].qs-card-summary .qs-card-metrics strong{font-size:23px;letter-spacing:-.5px;margin:0}[data-fastnet-card].qs-card-summary .qs-card-metrics>div+div{padding:0;border:0}[data-fastnet-card].qs-card-summary .qs-card-statuses>div{padding:0;border:0;background:none;max-width:50%}[data-fastnet-card].qs-card-summary .qs-card-statuses span{margin:0;gap:4px}[data-fastnet-card].qs-card-summary .qs-card-statuses i{width:4px;height:4px}[data-fastnet-card].qs-card-summary .qs-card-primary{padding:2px 7px;border-radius:6px}@media(max-width:600px){[data-fastnet-card]:not(.qs-card-summary) .fn-speed-stage{padding:14px;gap:12px}[data-fastnet-card]:not(.qs-card-summary) .qs-card-metrics strong{font-size:36px}[data-fastnet-card]:not(.qs-card-summary) .qs-card-metrics>div+div strong{font-size:28px}}[data-fastnet-card].fn-dense:not(.qs-card-summary){gap:6px;padding:12px 16px}[data-fastnet-card].fn-dense:not(.qs-card-summary) .fn-speed-stage{padding:10px 12px;gap:6px}[data-fastnet-card].fn-dense:not(.qs-card-summary) .fn-speed-caption{display:none}[data-fastnet-card].fn-dense:not(.qs-card-summary) .qs-card-metrics strong{font-size:32px;line-height:1.15;margin:0}[data-fastnet-card].fn-dense:not(.qs-card-summary) .qs-card-metrics>div+div strong{font-size:27px}[data-fastnet-card].fn-dense:not(.qs-card-summary) .qs-card-statuses>div{padding:6px 9px}[data-fastnet-card].fn-dense:not(.qs-card-summary) .qs-card-footer{display:none}', T = (r) => r && ["running", "cancel_requested"].includes(r.state), $ = ["running", "cancel_requested", "succeeded", "partial", "failed", "cancelled", "interrupted"];
function ue(r) {
  var v, h;
  if ((r == null ? void 0 : r.schemaVersion) !== 1 || !["ready", "disabled", "unavailable"].includes((v = r.service) == null ? void 0 : v.state) || !("latest" in r) || !("task" in r)) throw Error("invalid_summary");
  if ((h = r.latest) != null && h.bandwidth) {
    const e = r.latest.bandwidth;
    if (![e.downloadBps, e.uploadBps].every((i) => typeof i == "number" && Number.isFinite(i) && i >= 0) || !e.measuredAt || !Number.isFinite(Date.parse(e.measuredAt))) throw Error("invalid_bandwidth");
  }
  if (r.task && !$.includes(r.task.state)) throw Error("invalid_task");
  for (const e of ["download", "upload", "nat", "ipv6"]) if (r.latest) {
    const i = r.latest[e];
    if (!i || !["ok", "unavailable", "error", "not_tested"].includes(i.status) || i.value !== null && (["download", "upload"].includes(e) ? typeof i.value != "number" || !Number.isFinite(i.value) || i.value < 0 : typeof i.value != "string")) throw Error("invalid_measurement");
  }
  return r;
}
function pe(r) {
  const v = r == null ? void 0 : r.latest;
  return v ? v.bandwidth || { downloadBps: v.download.status === "ok" ? v.download.value : null, uploadBps: v.upload.status === "ok" ? v.upload.value : null, measuredAt: v.measuredAt } : null;
}
function W(r) {
  return r == null ? "—" : r > 0 && r < 1e5 ? "<0.1" : (r / 1e6).toLocaleString("en-US", { maximumFractionDigits: r >= 1e8 ? 0 : 1 });
}
function se(r, v) {
  return !r || !Number.isFinite(Date.parse(r)) ? "—" : new Date(r).toLocaleString(v === "en" ? "en-GB" : "zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: !1 });
}
const fe = (r) => !!(r && Date.now() - Date.parse(r) > 864e5);
function me(r, v = (e) => e, h = globalThis) {
  const e = v({ loading: !1, summary: null, task: null, submitting: !1, cancelling: !1, error: "", errorAction: "read", paused: !1, failures: 0 });
  let i = !0, t = !0, b, n, l, f = null, m = 0;
  const _ = () => {
    h.clearTimeout(b), b = void 0, n == null || n.abort(), n = void 0, m++;
  }, A = (u) => [401, 403].includes(u == null ? void 0 : u.status) ? "permission" : (u == null ? void 0 : u.status) === 404 ? "upgrade" : "unavailable", N = () => {
    i && t && T(e.task) && !e.paused && (b = h.setTimeout(S, 2e3));
  };
  function S() {
    return z(this, null, function* () {
      if (!i || !t || !T(e.task)) return;
      const u = e.task.id, y = ++m;
      n = new AbortController();
      try {
        const p = yield r.request("/task?id=" + encodeURIComponent(u), { signal: n.signal });
        if (!i || y !== m) return;
        if (p.id !== u || !$.includes(p.state)) throw Error("invalid_task");
        if (e.task = p, e.failures = 0, e.error = "", !T(p)) {
          f = null, yield C();
          return;
        }
      } catch (p) {
        if (!i || y !== m) return;
        e.failures++, e.error = A(p), e.errorAction = "read", (e.failures >= 3 || ["permission", "upgrade"].includes(e.error)) && (e.paused = !0);
      } finally {
        i && y === m && (n = void 0, N());
      }
    });
  }
  function C() {
    return z(this, null, function* () {
      if (_(), !i || !t) return;
      const u = m;
      e.loading = !0, n = new AbortController();
      try {
        const y = ue(yield r.request("/summary", { signal: n.signal }));
        if (!i || u !== m) return;
        e.summary = y, e.task = y.task || y.lastTask || null, e.error = "", e.failures = 0, e.paused = !1, T(e.task) && (f = null);
      } catch (y) {
        i && u === m && (e.error = A(y), e.errorAction = "read");
      } finally {
        i && u === m && (e.loading = !1, n = void 0, N());
      }
    });
  }
  function L() {
    return z(this, null, function* () {
      var y;
      if (!i || e.error === "permission" || e.submitting || T(e.task) || e.loading || ((y = e.summary) == null ? void 0 : y.service.state) !== "ready") return;
      _();
      const u = m;
      e.submitting = !0, e.error = "", l = new AbortController(), f || (f = Array.from(crypto.getRandomValues(new Uint8Array(16)), (p) => p.toString(16).padStart(2, "0")).join(""));
      try {
        const p = yield r.request("/run", { method: "POST", body: JSON.stringify({ idempotencyKey: f }), signal: l.signal });
        if (!i) return;
        if (!$.includes(p.state)) throw Error("invalid_task");
        if (f = null, u !== m) return;
        e.task = p, e.paused = !1, e.failures = 0, T(p) ? N() : yield C();
      } catch (p) {
        if (!i || u !== m) return;
        (p == null ? void 0 : p.status) === 409 ? (f = null, yield C()) : (e.error = A(p), e.errorAction = ["permission", "upgrade"].includes(e.error) ? "read" : "run", p != null && p.status && p.status < 500 && (f = null));
      } finally {
        i && (e.submitting = !1, l = void 0);
      }
    });
  }
  function F() {
    return z(this, null, function* () {
      if (!i || !T(e.task) || e.cancelling) return;
      _();
      const u = m;
      e.cancelling = !0, l = new AbortController();
      try {
        const y = yield r.request("/cancel", { method: "POST", body: JSON.stringify({ id: e.task.id }), signal: l.signal });
        if (!i || u !== m) return;
        e.task = y, T(y) ? N() : yield C();
      } catch (y) {
        i && u === m && (e.error = A(y), e.errorAction = "read", N());
      } finally {
        i && (e.cancelling = !1, l = void 0);
      }
    });
  }
  return { state: e, start: L, stop: F, reload: C, visibility(u) {
    t = u, _(), u && C();
  }, dispose() {
    i = !1, _(), l == null || l.abort();
  } };
}
const ge = { class: "qs-card-details" }, ve = { key: 0 }, be = {
  href: "/cgi-bin/luci/admin/services/fastnet/open",
  target: "_blank",
  rel: "noopener"
}, ye = {
  __name: "Details",
  props: ["state", "locale"],
  setup(r) {
    const v = r, h = ["download", "upload", "nat", "ipv6"], e = (b, n) => v.locale === "en" ? n : b, i = { download: e("下载", "Download"), upload: e("上传", "Upload"), nat: "NAT", ipv6: "IPv6" };
    function t(b) {
      var l, f;
      const n = (f = (l = v.state.summary) == null ? void 0 : l.latest) == null ? void 0 : f[b];
      return !n || n.status === "not_tested" ? e("未检测", "Not tested") : n.status === "error" ? e("检测失败", "Probe failed") : n.status === "unavailable" ? e("不可用", "Unavailable") : ["download", "upload"].includes(b) ? W(n.value) + " Mbps" : n.value;
    }
    return (b, n) => (x(), w("div", ge, [
      s("p", null, d(e("默认外网出口 · 路由器 → 互联网", "Default WAN route · Router → Internet")), 1),
      s("dl", null, [
        (x(), w(ee, null, re(h, (l) => {
          var f, m, _, A, N, S;
          return x(), w(ee, { key: l }, [
            s("dt", null, d(i[l]), 1),
            s("dd", null, [
              k(d(t(l)), 1),
              s("small", null, d(c(se)((_ = (m = (f = r.state.summary) == null ? void 0 : f.latest) == null ? void 0 : m[l]) == null ? void 0 : _.measuredAt, r.locale)), 1),
              (S = (N = (A = r.state.summary) == null ? void 0 : A.lastTask) == null ? void 0 : N.issues) != null && S[l] ? (x(), w("span", ve, d(e("本次探测失败，保留上次有效结果", "Latest probe failed; previous valid result retained")), 1)) : B("", !0)
            ])
          ], 64);
        }), 64))
      ]),
      s("p", null, d(e("测速会使用外网上传和下载带宽。NAT 与 IPv6 分别反映各自检测时间的结果。", "Testing uses WAN upload and download bandwidth. NAT and IPv6 describe their own detection times.")), 1),
      s("a", be, d(e("打开完整 FastNet", "Open full FastNet")), 1)
    ]));
  }
}, qe = ["data-task-id"], xe = { class: "qs-card-header" }, he = {
  key: 0,
  class: "widget-action-group"
}, ke = {
  key: 1,
  class: "qs-card-actions"
}, we = { class: "qs-card-menu" }, _e = ["aria-label"], Ae = { class: "fn-speed-stage" }, Ne = { class: "fn-speed-caption" }, Te = { class: "qs-card-metrics" }, Ce = { class: "qs-card-time" }, Se = ["datetime"], Fe = { class: "qs-card-statuses" }, Pe = ["data-tone"], Ee = ["title"], De = ["data-tone"], ze = ["title"], Be = {
  key: 0,
  class: "qs-card-progress",
  role: "status"
}, Ie = ["disabled"], Le = {
  key: 1,
  class: "qs-card-alert",
  role: "alert"
}, Re = {
  key: 2,
  class: "qs-card-alert",
  role: "status"
}, Oe = {
  key: 3,
  class: "qs-card-note",
  role: "status"
}, Ve = {
  key: 4,
  class: "qs-card-alert",
  role: "status"
}, Me = { class: "qs-card-footer" }, We = {
  __name: "Card",
  props: ["context"],
  setup(r) {
    const v = ne({ loader: () => import("./chunk.5e62b45e.js"), timeout: 8e3, errorComponent: { render: () => V("p", { role: "alert", style: "padding:24px" }, [V("span", "FastNet 暂时无法打开 / Unable to open FastNet. "), V("a", { href: "/cgi-bin/luci/admin/services/fastnet/open", target: "_blank", rel: "noopener" }, "新窗口打开 / Open in new window ↗")]) } }), h = r, e = h.context, i = e.locale === "en" ? "en" : "zh-cn", t = (o, a) => i === "en" ? a : o, b = me(e, le), n = b.state, l = "/cgi-bin/luci/admin/services/fastnet", f = E(() => pe(n.summary)), m = E(() => T(n.task)), _ = { preparing: t("准备测速", "Preparing"), ping: t("检测延迟", "Testing latency"), download: t("测试下载", "Testing download"), upload: t("测试上传", "Testing upload"), nat: t("检测 NAT", "Checking NAT"), ipv6: t("检测 IPv6", "Checking IPv6") }, A = E(() => {
      var o, a;
      return ((o = n.task) == null ? void 0 : o.state) === "cancel_requested" ? t("正在停止", "Stopping") : _[(a = n.task) == null ? void 0 : a.stage] || t("测速中", "Testing");
    }), N = E(() => n.error === "permission" ? t("登录已失效或权限不足，请重新登录", "Session expired or permission denied; sign in again") : n.error === "upgrade" ? t("插件接口不可用，请检查或升级 FastNet", "Plugin API unavailable; check or update FastNet") : n.paused ? t("连接连续失败，已暂停查询；后台任务继续运行", "Queries paused after repeated failures; the background task continues") : t("暂时无法确认结果，保留已有数据", "Result unavailable; existing data retained")), S = E(() => {
      var o;
      return { failed: t("本次测速失败，保留上次结果", "Test failed; previous results retained"), partial: t("部分检测未完成，已保留各项有效结果", "Some probes failed; valid results retained"), cancelled: t("已停止，保留上次结果", "Stopped; previous results retained"), interrupted: t("任务已中断，可重新测速", "Task interrupted; start a new test") }[(o = n.task) == null ? void 0 : o.state];
    }), C = E(() => [{ id: "details", label: t("查看上次结果", "Last result details") }, { id: "reload", label: t("重新读取", "Reload") }, { id: "settings", label: t("插件设置", "Plugin settings") }, { id: "full", label: t("完整 FastNet", "Full FastNet") }]);
    function L(o) {
      o === "details" ? J() : o === "reload" ? b.reload() : o === "settings" ? window.open(l, "_blank", "noopener") : o === "full" && P();
    }
    const F = M(!1), u = M(null), y = M(!1);
    let p;
    function j(o) {
      var g, q;
      const a = (q = (g = n.summary) == null ? void 0 : g.latest) == null ? void 0 : q[o];
      return R(o) || (a == null ? void 0 : a.status) === "error" ? "warning" : (a == null ? void 0 : a.status) === "ok" ? "good" : "neutral";
    }
    function P(o) {
      var g, q;
      const a = (g = o == null ? void 0 : o.currentTarget) == null ? void 0 : g.closest("details");
      a == null || a.removeAttribute("open"), (q = a == null ? void 0 : a.querySelector("summary")) == null || q.focus({ preventScroll: !0 }), F.value = !0, b.visibility(!1), e.openDetails(v, { context: e, locale: i }, { wide: !0, onClose() {
        F.value = !1, b.visibility(!document.hidden && !F.value);
      } });
    }
    const R = (o) => {
      var a, g, q;
      return !m.value && !!((q = (g = (a = n.summary) == null ? void 0 : a.lastTask) == null ? void 0 : g.issues) != null && q[o]);
    };
    function I(o) {
      var q, D;
      const a = (D = (q = n.summary) == null ? void 0 : q.latest) == null ? void 0 : D[o];
      let g;
      return !a || a.status === "not_tested" ? g = t("未检测", "Not tested") : a.status === "error" ? g = t("检测失败", "Probe failed") : a.status === "unavailable" ? g = t("不可用", "Unavailable") : o === "ipv6" ? g = /部分|准备度 [0-9]\/10/.test(a.value) ? t("部分可用", "Partly available") : t("可用", "Available") : g = /port.?restricted/i.test(a.value) ? t("端口受限锥形", "Port Restricted Cone") : /restricted.*cone/i.test(a.value) ? t("受限锥形", "Restricted Cone") : /full.?cone/i.test(a.value) ? t("全锥形", "Full Cone") : /symmetric/i.test(a.value) ? t("对称型", "Symmetric") : a.value, R(o) ? g + " · " + t("本次失败", "latest failed") : g;
    }
    function J(o) {
      var g, q;
      const a = (g = o == null ? void 0 : o.currentTarget) == null ? void 0 : g.closest("details");
      a == null || a.removeAttribute("open"), (q = a == null ? void 0 : a.querySelector("summary")) == null || q.focus({ preventScroll: !0 }), e.openDetails(ye, { state: n, locale: i });
    }
    function O() {
      b.visibility(!document.hidden && !F.value);
    }
    return ie(() => {
      p = new ResizeObserver(() => {
        var o;
        y.value = ((o = u.value) == null ? void 0 : o.clientHeight) < 300;
      }), u.value && p.observe(u.value), document.addEventListener("visibilitychange", O), O();
    }), de(() => {
      p == null || p.disconnect(), document.removeEventListener("visibilitychange", O), b.dispose();
    }), (o, a) => {
      var g, q, D, G, H, K, Q, X, Y;
      return x(), w("article", {
        ref_key: "root",
        ref: u,
        class: U(["qs-card-content", { "qs-card-summary": c(e).form === "summary", "fn-dense": y.value }]),
        "data-fastnet-card": "",
        "data-task-id": m.value ? c(n).task.id : void 0
      }, [
        s("header", xe, [
          s("h2", null, [
            a[3] || (a[3] = s("svg", {
              viewBox: "0 0 24 24",
              "aria-hidden": "true"
            }, [
              s("path", { d: "M3 12h4l3-8 4 16 3-8h4" })
            ], -1)),
            k(d(t("外网测速", "Internet speed")), 1)
          ]),
          (g = c(e).components) != null && g.PrimaryAction && ((q = c(e).components) != null && q.Menu) ? (x(), w("div", he, [
            (x(), te(ae(c(e).components.PrimaryAction), {
              icon: "activity",
              "data-fastnet-test": "",
              onClick: P
            }, {
              default: oe(() => [
                k(d(m.value ? t("查看进度", "View progress") : t("测速", "Test")), 1)
              ]),
              _: 1
            })),
            (x(), te(ae(c(e).components.Menu), {
              label: t("外网测速更多操作", "Internet speed actions"),
              items: C.value,
              onSelect: L
            }, null, 40, ["label", "items"]))
          ])) : (x(), w("div", ke, [
            s("button", {
              class: "qs-card-primary",
              "data-fastnet-test": "",
              onClick: P
            }, d(m.value ? t("查看进度", "View progress") : t("测速", "Test")), 1),
            s("details", we, [
              s("summary", {
                "aria-label": t("外网测速更多操作", "Internet speed actions")
              }, "⋮", 8, _e),
              s("div", null, [
                s("button", {
                  "data-fastnet-details": "",
                  onClick: J
                }, d(t("查看上次结果", "Last result details")), 1),
                s("button", {
                  onClick: a[0] || (a[0] = (Z) => c(b).reload())
                }, d(t("重新读取", "Reload")), 1),
                s("a", {
                  href: l,
                  target: "_blank",
                  rel: "noopener"
                }, d(t("插件设置", "Plugin settings")), 1),
                s("button", { onClick: P }, d(t("完整 FastNet", "Full FastNet")), 1)
              ])
            ])
          ]))
        ]),
        s("div", Ae, [
          s("div", Ne, [
            s("span", null, "WAN · " + d(t("最近一次测速", "LAST SPEED TEST")), 1),
            s("span", {
              class: U(["fn-live", { "is-active": m.value }])
            }, d(m.value ? A.value : (D = f.value) != null && D.measuredAt ? t("已保存", "Saved") : t("等待测速", "Ready to test")), 3)
          ]),
          s("div", Te, [
            s("div", null, [
              s("span", null, "↓ " + d(t("上次下载", "Last download")), 1),
              s("strong", null, [
                k(d(c(W)((G = f.value) == null ? void 0 : G.downloadBps)), 1),
                a[4] || (a[4] = s("small", null, "Mbps", -1))
              ])
            ]),
            s("div", null, [
              s("span", null, "↑ " + d(t("上次上传", "Last upload")), 1),
              s("strong", null, [
                k(d(c(W)((H = f.value) == null ? void 0 : H.uploadBps)), 1),
                a[5] || (a[5] = s("small", null, "Mbps", -1))
              ])
            ])
          ]),
          s("p", Ce, [
            k(d(t("上次测速", "Last tested")) + " ", 1),
            s("time", {
              datetime: ((K = f.value) == null ? void 0 : K.measuredAt) || void 0
            }, d((Q = f.value) != null && Q.measuredAt ? c(se)(f.value.measuredAt, c(i)) : t("尚未测速", "No test yet")), 9, Se)
          ])
        ]),
        s("div", Fe, [
          s("div", {
            "data-tone": j("nat")
          }, [
            a[6] || (a[6] = s("span", null, [
              s("i", { "aria-hidden": "true" }),
              k("NAT")
            ], -1)),
            s("strong", {
              title: I("nat")
            }, d(I("nat")), 9, Ee)
          ], 8, Pe),
          s("div", {
            "data-tone": j("ipv6")
          }, [
            a[7] || (a[7] = s("span", null, [
              s("i", { "aria-hidden": "true" }),
              k("IPv6")
            ], -1)),
            s("strong", {
              class: U({ "qs-card-warning": R("ipv6") }),
              title: I("ipv6")
            }, d(I("ipv6")), 11, ze)
          ], 8, De)
        ]),
        m.value ? (x(), w("div", Be, [
          s("span", null, [
            k(d(A.value), 1),
            s("small", null, d(t("上次有效结果保持显示", "Previous valid results remain visible")), 1)
          ]),
          s("button", {
            disabled: c(n).cancelling || c(n).task.state === "cancel_requested",
            onClick: a[1] || (a[1] = (Z) => c(b).stop())
          }, d(c(n).cancelling || c(n).task.state === "cancel_requested" ? t("正在停止", "Stopping") : t("停止", "Stop")), 9, Ie)
        ])) : B("", !0),
        c(n).error ? (x(), w("p", Le, [
          k(d(N.value) + " ", 1),
          s("button", {
            onClick: a[2] || (a[2] = (Z) => c(n).errorAction === "run" ? P() : c(b).reload())
          }, d(c(n).paused ? t("恢复查询", "Resume queries") : t("重试", "Retry")), 1)
        ])) : c(n).summary && c(n).summary.service.state !== "ready" ? (x(), w("p", Re, [
          k(d(c(n).summary.service.state === "disabled" ? t("服务未启用", "Service disabled") : t("服务暂不可用", "Service unavailable")) + " ", 1),
          s("a", { href: l }, d(t("打开设置", "Open settings")), 1)
        ])) : c(n).task && ["failed", "cancelled", "interrupted", "partial"].includes(c(n).task.state) ? (x(), w("p", Oe, [
          k(d(S.value) + " ", 1),
          c(n).task.state === "failed" ? (x(), w("button", {
            key: 0,
            onClick: P
          }, d(t("重试测速", "Retry test")), 1)) : B("", !0)
        ])) : B("", !0),
        (X = c(n).summary) != null && X.service.persistenceError ? (x(), w("p", Ve, d(t("结果保存失败，请检查设备存储", "Result could not be saved; check device storage")), 1)) : B("", !0),
        s("footer", Me, [
          s("span", null, [
            a[8] || (a[8] = s("span", {
              class: "fn-route-dot",
              "aria-hidden": "true"
            }, null, -1)),
            k(d(c(fe)((Y = f.value) == null ? void 0 : Y.measuredAt) ? t("结果较早，可重新测速", "Older result; test again") : t("默认外网出口", "Default WAN route")), 1)
          ]),
          a[9] || (a[9] = s("small", null, [
            k("FASTNET "),
            s("span", { "aria-hidden": "true" }, "↗")
          ], -1))
        ])
      ], 10, qe);
    };
  }
};
if (!document.getElementById("fastnet-card-v1-style")) {
  const r = document.createElement("style");
  r.id = "fastnet-card-v1-style", r.textContent = ce, document.head.appendChild(r);
}
const je = 1;
export {
  je as apiVersion,
  We as default
};
