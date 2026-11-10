var P = (r, v, y) => new Promise((e, i) => {
  var t = (o) => {
    try {
      n(y.next(o));
    } catch (c) {
      i(c);
    }
  }, b = (o) => {
    try {
      n(y.throw(o));
    } catch (c) {
      i(c);
    }
  }, n = (o) => o.done ? e(o.value) : Promise.resolve(o.value).then(t, b);
  n((y = y.apply(r, v)).next());
});
import { openBlock as k, createElementBlock as _, createElementVNode as s, toDisplayString as d, Fragment as K, renderList as Y, createTextVNode as h, unref as m, createCommentVNode as D, defineAsyncComponent as Z, h as O, computed as E, ref as U, onMounted as ee, onUnmounted as te, normalizeClass as V, reactive as ae } from "/luci-static/quickstart/card-runtime-v1.js";
const se = '[data-fastnet-card]{--fn-down:var(--qs-card-accent);position:relative;isolation:isolate;gap:14px;background:linear-gradient(145deg,transparent 48%,#7b9ee909);border-radius:inherit}[data-fastnet-card] .qs-card-header h2>svg{color:var(--fn-down)}[data-fastnet-card] .qs-card-primary{background:var(--qs-card-accent);color:var(--qs-card-panel);border-color:transparent;padding:6px 13px;border-radius:9px;font-weight:600}[data-fastnet-card] .qs-card-menu>summary{border-color:transparent;color:var(--qs-card-muted)}[data-fastnet-card] .fn-speed-stage{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:center;gap:14px;padding:18px 20px;border-radius:14px;border:1px solid var(--qs-card-line);background:linear-gradient(120deg,#608ee90c,transparent 75%),var(--qs-card-soft)}[data-fastnet-card] .fn-speed-caption{display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:10px;letter-spacing:.7px;color:var(--qs-card-muted)}[data-fastnet-card] .fn-live{display:flex;align-items:center;gap:5px;letter-spacing:0;white-space:nowrap}[data-fastnet-card] .fn-live:before{content:"";width:5px;height:5px;border-radius:50%;background:var(--qs-card-muted)}[data-fastnet-card] .fn-live.is-active{color:var(--qs-card-accent)}[data-fastnet-card] .fn-live.is-active:before{background:currentColor;box-shadow:0 0 0 3px #6794ef20}[data-fastnet-card] .qs-card-metrics{gap:18px;align-items:center;grid-template-columns:1.25fr 1fr}[data-fastnet-card] .qs-card-metrics strong{font-size:clamp(30px,3.5vw,52px);line-height:1.15;letter-spacing:-1.7px;font-weight:700;margin-top:4px;color:var(--fn-down)}[data-fastnet-card] .qs-card-metrics>div+div{border-left:1px solid var(--qs-card-line);padding-left:18px}[data-fastnet-card] .qs-card-metrics>div+div strong{font-size:clamp(25px,2.5vw,36px);color:var(--qs-card-text);letter-spacing:-.9px}[data-fastnet-card] .qs-card-metrics small{letter-spacing:0}[data-fastnet-card] .qs-card-time{gap:5px;font-size:10px}[data-fastnet-card] .qs-card-statuses{padding:0;border:0;gap:10px}[data-fastnet-card] .qs-card-statuses>div{padding:10px 12px;border:1px solid var(--qs-card-line);border-radius:10px;background:var(--qs-card-panel)}[data-fastnet-card] .qs-card-statuses span{display:flex;align-items:center;gap:6px;letter-spacing:.3px;margin-bottom:3px}[data-fastnet-card] .qs-card-statuses i{width:6px;height:6px;border-radius:50%;background:var(--qs-card-muted)}[data-fastnet-card] .qs-card-statuses [data-tone=good] i{background:var(--qs-card-good)}[data-fastnet-card] .qs-card-statuses [data-tone=warning] i{background:var(--qs-card-warning)}[data-fastnet-card] .qs-card-footer{margin-top:0;align-items:center;font-size:10px}[data-fastnet-card] .qs-card-footer>span{display:flex;align-items:center;gap:6px}[data-fastnet-card] .fn-route-dot{width:5px;height:5px;border:1px solid var(--qs-card-muted);border-radius:50%}[data-fastnet-card] .qs-card-footer small{letter-spacing:1.5px;font-size:9px}[data-fastnet-card].qs-card-summary{gap:3px;background:none}[data-fastnet-card].qs-card-summary .fn-speed-stage{display:block;flex:none;padding:0;border:0;background:none}[data-fastnet-card].qs-card-summary .fn-speed-caption{display:none}[data-fastnet-card].qs-card-summary .qs-card-metrics{grid-template-columns:1fr 1fr;gap:12px}[data-fastnet-card].qs-card-summary .qs-card-metrics strong{font-size:23px;letter-spacing:-.5px;margin:0}[data-fastnet-card].qs-card-summary .qs-card-metrics>div+div{padding:0;border:0}[data-fastnet-card].qs-card-summary .qs-card-statuses>div{padding:0;border:0;background:none;max-width:50%}[data-fastnet-card].qs-card-summary .qs-card-statuses span{margin:0;gap:4px}[data-fastnet-card].qs-card-summary .qs-card-statuses i{width:4px;height:4px}[data-fastnet-card].qs-card-summary .qs-card-primary{padding:2px 7px;border-radius:6px}.fn-web-dialog{width:100%;min-width:0;min-height:0;display:flex;flex-direction:column;background:var(--qs-card-panel);color:var(--qs-card-text)}.fn-web-toolbar{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px;padding:10px 20px;border-bottom:1px solid var(--qs-card-line);font-size:11px;letter-spacing:1px}.fn-web-toolbar small{letter-spacing:0;color:var(--qs-card-muted)}.fn-web-toolbar a{color:var(--qs-card-accent);letter-spacing:0;padding:4px}.fn-web-frame{position:relative;flex:1;min-height:0}.fn-web-frame iframe{display:block;border:0;width:100%;height:100%;background:var(--qs-card-panel)}.fn-web-loading{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:24px;text-align:center;background:var(--qs-card-panel);color:var(--qs-card-muted)}.fn-web-loading strong{color:var(--qs-card-text);font-size:16px}.fn-web-loading p{font-size:12px;line-height:1.7;max-width:360px;margin:0}.fn-web-loading button{font:inherit;color:var(--qs-card-accent);border:1px solid var(--qs-card-line);background:var(--qs-card-soft);padding:10px 20px;border-radius:8px;cursor:pointer}.fn-web-footnote{font-size:10px;color:var(--qs-card-muted);line-height:1.6;margin:0!important;padding:9px 20px;border-top:1px solid var(--qs-card-line)}@media(max-width:600px){[data-fastnet-card]:not(.qs-card-summary) .fn-speed-stage{padding:14px;gap:12px}[data-fastnet-card]:not(.qs-card-summary) .qs-card-metrics strong{font-size:36px}[data-fastnet-card]:not(.qs-card-summary) .qs-card-metrics>div+div strong{font-size:28px}.fn-web-toolbar{padding:8px 14px}.fn-web-toolbar small{display:none}.fn-web-footnote{padding:8px 14px}}[data-fastnet-card].fn-dense:not(.qs-card-summary){gap:6px;padding:12px 16px}[data-fastnet-card].fn-dense:not(.qs-card-summary) .fn-speed-stage{padding:10px 12px;gap:6px}[data-fastnet-card].fn-dense:not(.qs-card-summary) .fn-speed-caption{display:none}[data-fastnet-card].fn-dense:not(.qs-card-summary) .qs-card-metrics strong{font-size:32px;line-height:1.15;margin:0}[data-fastnet-card].fn-dense:not(.qs-card-summary) .qs-card-metrics>div+div strong{font-size:27px}[data-fastnet-card].fn-dense:not(.qs-card-summary) .qs-card-statuses>div{padding:6px 9px}[data-fastnet-card].fn-dense:not(.qs-card-summary) .qs-card-footer{display:none}', S = (r) => r && ["running", "cancel_requested"].includes(r.state), $ = ["running", "cancel_requested", "succeeded", "partial", "failed", "cancelled", "interrupted"];
function re(r) {
  var v, y;
  if ((r == null ? void 0 : r.schemaVersion) !== 1 || !["ready", "disabled", "unavailable"].includes((v = r.service) == null ? void 0 : v.state) || !("latest" in r) || !("task" in r)) throw Error("invalid_summary");
  if ((y = r.latest) != null && y.bandwidth) {
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
function ne(r) {
  const v = r == null ? void 0 : r.latest;
  return v ? v.bandwidth || { downloadBps: v.download.status === "ok" ? v.download.value : null, uploadBps: v.upload.status === "ok" ? v.upload.value : null, measuredAt: v.measuredAt } : null;
}
function W(r) {
  return r == null ? "—" : r > 0 && r < 1e5 ? "<0.1" : (r / 1e6).toLocaleString("en-US", { maximumFractionDigits: r >= 1e8 ? 0 : 1 });
}
function Q(r, v) {
  return !r || !Number.isFinite(Date.parse(r)) ? "—" : new Date(r).toLocaleString(v === "en" ? "en-GB" : "zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: !1 });
}
const ie = (r) => !!(r && Date.now() - Date.parse(r) > 864e5);
function de(r, v = (e) => e, y = globalThis) {
  const e = v({ loading: !1, summary: null, task: null, submitting: !1, cancelling: !1, error: "", errorAction: "read", paused: !1, failures: 0 });
  let i = !0, t = !0, b, n, o, c = null, f = 0;
  const A = () => {
    y.clearTimeout(b), b = void 0, n == null || n.abort(), n = void 0, f++;
  }, N = (l) => [401, 403].includes(l == null ? void 0 : l.status) ? "permission" : (l == null ? void 0 : l.status) === 404 ? "upgrade" : "unavailable", T = () => {
    i && t && S(e.task) && !e.paused && (b = y.setTimeout(C, 2e3));
  };
  function C() {
    return P(this, null, function* () {
      if (!i || !t || !S(e.task)) return;
      const l = e.task.id, x = ++f;
      n = new AbortController();
      try {
        const u = yield r.request("/task?id=" + encodeURIComponent(l), { signal: n.signal });
        if (!i || x !== f) return;
        if (u.id !== l || !$.includes(u.state)) throw Error("invalid_task");
        if (e.task = u, e.failures = 0, e.error = "", !S(u)) {
          c = null, yield w();
          return;
        }
      } catch (u) {
        if (!i || x !== f) return;
        e.failures++, e.error = N(u), e.errorAction = "read", (e.failures >= 3 || ["permission", "upgrade"].includes(e.error)) && (e.paused = !0);
      } finally {
        i && x === f && (n = void 0, T());
      }
    });
  }
  function w() {
    return P(this, null, function* () {
      if (A(), !i || !t) return;
      const l = f;
      e.loading = !0, n = new AbortController();
      try {
        const x = re(yield r.request("/summary", { signal: n.signal }));
        if (!i || l !== f) return;
        e.summary = x, e.task = x.task || x.lastTask || null, e.error = "", e.failures = 0, e.paused = !1, S(e.task) && (c = null);
      } catch (x) {
        i && l === f && (e.error = N(x), e.errorAction = "read");
      } finally {
        i && l === f && (e.loading = !1, n = void 0, T());
      }
    });
  }
  function z() {
    return P(this, null, function* () {
      var x;
      if (!i || e.error === "permission" || e.submitting || S(e.task) || e.loading || ((x = e.summary) == null ? void 0 : x.service.state) !== "ready") return;
      A();
      const l = f;
      e.submitting = !0, e.error = "", o = new AbortController(), c || (c = Array.from(crypto.getRandomValues(new Uint8Array(16)), (u) => u.toString(16).padStart(2, "0")).join(""));
      try {
        const u = yield r.request("/run", { method: "POST", body: JSON.stringify({ idempotencyKey: c }), signal: o.signal });
        if (!i) return;
        if (!$.includes(u.state)) throw Error("invalid_task");
        if (c = null, l !== f) return;
        e.task = u, e.paused = !1, e.failures = 0, S(u) ? T() : yield w();
      } catch (u) {
        if (!i || l !== f) return;
        (u == null ? void 0 : u.status) === 409 ? (c = null, yield w()) : (e.error = N(u), e.errorAction = ["permission", "upgrade"].includes(e.error) ? "read" : "run", u != null && u.status && u.status < 500 && (c = null));
      } finally {
        i && (e.submitting = !1, o = void 0);
      }
    });
  }
  function B() {
    return P(this, null, function* () {
      if (!i || !S(e.task) || e.cancelling) return;
      A();
      const l = f;
      e.cancelling = !0, o = new AbortController();
      try {
        const x = yield r.request("/cancel", { method: "POST", body: JSON.stringify({ id: e.task.id }), signal: o.signal });
        if (!i || l !== f) return;
        e.task = x, S(x) ? T() : yield w();
      } catch (x) {
        i && l === f && (e.error = N(x), e.errorAction = "read", T());
      } finally {
        i && (e.cancelling = !1, o = void 0);
      }
    });
  }
  return { state: e, start: z, stop: B, reload: w, visibility(l) {
    t = l, A(), l && w();
  }, dispose() {
    i = !1, A(), o == null || o.abort();
  } };
}
const oe = { class: "qs-card-details" }, le = { key: 0 }, ce = {
  href: "/cgi-bin/luci/admin/services/fastnet/open",
  target: "_blank",
  rel: "noopener"
}, ue = {
  __name: "Details",
  props: ["state", "locale"],
  setup(r) {
    const v = r, y = ["download", "upload", "nat", "ipv6"], e = (b, n) => v.locale === "en" ? n : b, i = { download: e("下载", "Download"), upload: e("上传", "Upload"), nat: "NAT", ipv6: "IPv6" };
    function t(b) {
      var o, c;
      const n = (c = (o = v.state.summary) == null ? void 0 : o.latest) == null ? void 0 : c[b];
      return !n || n.status === "not_tested" ? e("未检测", "Not tested") : n.status === "error" ? e("检测失败", "Probe failed") : n.status === "unavailable" ? e("不可用", "Unavailable") : ["download", "upload"].includes(b) ? W(n.value) + " Mbps" : n.value;
    }
    return (b, n) => (k(), _("div", oe, [
      s("p", null, d(e("默认外网出口 · 路由器 → 互联网", "Default WAN route · Router → Internet")), 1),
      s("dl", null, [
        (k(), _(K, null, Y(y, (o) => {
          var c, f, A, N, T, C;
          return k(), _(K, { key: o }, [
            s("dt", null, d(i[o]), 1),
            s("dd", null, [
              h(d(t(o)), 1),
              s("small", null, d(m(Q)((A = (f = (c = r.state.summary) == null ? void 0 : c.latest) == null ? void 0 : f[o]) == null ? void 0 : A.measuredAt, r.locale)), 1),
              (C = (T = (N = r.state.summary) == null ? void 0 : N.lastTask) == null ? void 0 : T.issues) != null && C[o] ? (k(), _("span", le, d(e("本次探测失败，保留上次有效结果", "Latest probe failed; previous valid result retained")), 1)) : D("", !0)
            ])
          ], 64);
        }), 64))
      ]),
      s("p", null, d(e("测速会使用外网上传和下载带宽。NAT 与 IPv6 分别反映各自检测时间的结果。", "Testing uses WAN upload and download bandwidth. NAT and IPv6 describe their own detection times.")), 1),
      s("a", ce, d(e("打开完整 FastNet", "Open full FastNet")), 1)
    ]));
  }
}, pe = ["data-task-id"], fe = { class: "qs-card-header" }, me = { class: "qs-card-actions" }, ge = { class: "qs-card-menu" }, ve = ["aria-label"], be = { class: "fn-speed-stage" }, xe = { class: "fn-speed-caption" }, ye = { class: "qs-card-metrics" }, qe = { class: "qs-card-time" }, he = ["datetime"], we = { class: "qs-card-statuses" }, ke = ["data-tone"], _e = ["title"], Ae = ["data-tone"], Ne = ["title"], Te = {
  key: 0,
  class: "qs-card-progress",
  role: "status"
}, Se = ["disabled"], Ce = {
  key: 1,
  class: "qs-card-alert",
  role: "alert"
}, ze = {
  key: 2,
  class: "qs-card-alert",
  role: "status"
}, Fe = {
  key: 3,
  class: "qs-card-note",
  role: "status"
}, Pe = {
  key: 4,
  class: "qs-card-alert",
  role: "status"
}, Ee = { class: "qs-card-footer" }, Le = {
  __name: "Card",
  props: ["context"],
  setup(r) {
    const v = Z({ loader: () => import("./chunk.62c86bd5.js"), timeout: 8e3, errorComponent: { render: () => O("p", { role: "alert", style: "padding:24px" }, [O("span", "FastNet 暂时无法打开 / Unable to open FastNet. "), O("a", { href: "/cgi-bin/luci/admin/services/fastnet/open", target: "_blank", rel: "noopener" }, "新窗口打开 / Open in new window ↗")]) } }), y = r, e = y.context, i = e.locale === "en" ? "en" : "zh-cn", t = (p, a) => i === "en" ? a : p, b = de(e, ae), n = b.state, o = "/cgi-bin/luci/admin/services/fastnet", c = E(() => ne(n.summary)), f = E(() => S(n.task)), A = { preparing: t("准备测速", "Preparing"), ping: t("检测延迟", "Testing latency"), download: t("测试下载", "Testing download"), upload: t("测试上传", "Testing upload"), nat: t("检测 NAT", "Checking NAT"), ipv6: t("检测 IPv6", "Checking IPv6") }, N = E(() => {
      var p, a;
      return ((p = n.task) == null ? void 0 : p.state) === "cancel_requested" ? t("正在停止", "Stopping") : A[(a = n.task) == null ? void 0 : a.stage] || t("测速中", "Testing");
    }), T = E(() => n.error === "permission" ? t("登录已失效或权限不足，请重新登录", "Session expired or permission denied; sign in again") : n.error === "upgrade" ? t("插件接口不可用，请检查或升级 FastNet", "Plugin API unavailable; check or update FastNet") : n.paused ? t("连接连续失败，已暂停查询；后台任务继续运行", "Queries paused after repeated failures; the background task continues") : t("暂时无法确认结果，保留已有数据", "Result unavailable; existing data retained")), C = E(() => {
      var p;
      return { failed: t("本次测速失败，保留上次结果", "Test failed; previous results retained"), partial: t("部分检测未完成，已保留各项有效结果", "Some probes failed; valid results retained"), cancelled: t("已停止，保留上次结果", "Stopped; previous results retained"), interrupted: t("任务已中断，可重新测速", "Task interrupted; start a new test") }[(p = n.task) == null ? void 0 : p.state];
    }), w = U(!1), z = U(null), B = U(!1);
    let l;
    function x(p) {
      var g, q;
      const a = (q = (g = n.summary) == null ? void 0 : g.latest) == null ? void 0 : q[p];
      return R(p) || (a == null ? void 0 : a.status) === "error" ? "warning" : (a == null ? void 0 : a.status) === "ok" ? "good" : "neutral";
    }
    function u(p) {
      var g, q;
      const a = (g = p == null ? void 0 : p.currentTarget) == null ? void 0 : g.closest("details");
      a == null || a.removeAttribute("open"), (q = a == null ? void 0 : a.querySelector("summary")) == null || q.focus({ preventScroll: !0 }), w.value = !0, b.visibility(!1), e.openDetails(v, { context: e, locale: i }, { wide: !0, onClose() {
        w.value = !1, b.visibility(!document.hidden && !w.value);
      } });
    }
    const R = (p) => {
      var a, g, q;
      return !f.value && !!((q = (g = (a = n.summary) == null ? void 0 : a.lastTask) == null ? void 0 : g.issues) != null && q[p]);
    };
    function L(p) {
      var q, F;
      const a = (F = (q = n.summary) == null ? void 0 : q.latest) == null ? void 0 : F[p];
      let g;
      return !a || a.status === "not_tested" ? g = t("未检测", "Not tested") : a.status === "error" ? g = t("检测失败", "Probe failed") : a.status === "unavailable" ? g = t("不可用", "Unavailable") : p === "ipv6" ? g = /部分|准备度 [0-9]\/10/.test(a.value) ? t("部分可用", "Partly available") : t("可用", "Available") : g = /port.?restricted/i.test(a.value) ? t("端口受限锥形", "Port Restricted Cone") : /restricted.*cone/i.test(a.value) ? t("受限锥形", "Restricted Cone") : /full.?cone/i.test(a.value) ? t("全锥形", "Full Cone") : /symmetric/i.test(a.value) ? t("对称型", "Symmetric") : a.value, R(p) ? g + " · " + t("本次失败", "latest failed") : g;
    }
    function X(p) {
      var g;
      const a = p.currentTarget.closest("details");
      a == null || a.removeAttribute("open"), (g = a == null ? void 0 : a.querySelector("summary")) == null || g.focus({ preventScroll: !0 }), e.openDetails(ue, { state: n, locale: i });
    }
    function I() {
      b.visibility(!document.hidden && !w.value);
    }
    return ee(() => {
      l = new ResizeObserver(() => {
        var p;
        B.value = ((p = z.value) == null ? void 0 : p.clientHeight) < 300;
      }), z.value && l.observe(z.value), document.addEventListener("visibilitychange", I), I();
    }), te(() => {
      l == null || l.disconnect(), document.removeEventListener("visibilitychange", I), b.dispose();
    }), (p, a) => {
      var g, q, F, j, M, J, G;
      return k(), _("article", {
        ref_key: "root",
        ref: z,
        class: V(["qs-card-content", { "qs-card-summary": m(e).form === "summary", "fn-dense": B.value }]),
        "data-fastnet-card": "",
        "data-task-id": f.value ? m(n).task.id : void 0
      }, [
        s("header", fe, [
          s("h2", null, [
            a[3] || (a[3] = s("svg", {
              viewBox: "0 0 24 24",
              "aria-hidden": "true"
            }, [
              s("path", { d: "M3 12h4l3-8 4 16 3-8h4" })
            ], -1)),
            h(d(t("外网测速", "Internet speed")), 1)
          ]),
          s("div", me, [
            s("button", {
              class: "qs-card-primary",
              "data-fastnet-test": "",
              onClick: u
            }, [
              h(d(f.value ? t("查看进度", "View progress") : t("测速", "Test")), 1),
              a[4] || (a[4] = s("span", { "aria-hidden": "true" }, " ↗", -1))
            ]),
            s("details", ge, [
              s("summary", {
                "aria-label": t("外网测速更多操作", "Internet speed actions")
              }, "⋮", 8, ve),
              s("div", null, [
                s("button", {
                  "data-fastnet-details": "",
                  onClick: X
                }, d(t("查看上次结果", "Last result details")), 1),
                s("button", {
                  onClick: a[0] || (a[0] = (H) => m(b).reload())
                }, d(t("重新读取", "Reload")), 1),
                s("a", {
                  href: o,
                  target: "_blank",
                  rel: "noopener"
                }, d(t("插件设置", "Plugin settings")), 1),
                s("button", { onClick: u }, d(t("完整 FastNet", "Full FastNet")), 1)
              ])
            ])
          ])
        ]),
        s("div", be, [
          s("div", xe, [
            s("span", null, "WAN · " + d(t("最近一次测速", "LAST SPEED TEST")), 1),
            s("span", {
              class: V(["fn-live", { "is-active": f.value }])
            }, d(f.value ? N.value : (g = c.value) != null && g.measuredAt ? t("已保存", "Saved") : t("等待测速", "Ready to test")), 3)
          ]),
          s("div", ye, [
            s("div", null, [
              s("span", null, "↓ " + d(t("上次下载", "Last download")), 1),
              s("strong", null, [
                h(d(m(W)((q = c.value) == null ? void 0 : q.downloadBps)), 1),
                a[5] || (a[5] = s("small", null, "Mbps", -1))
              ])
            ]),
            s("div", null, [
              s("span", null, "↑ " + d(t("上次上传", "Last upload")), 1),
              s("strong", null, [
                h(d(m(W)((F = c.value) == null ? void 0 : F.uploadBps)), 1),
                a[6] || (a[6] = s("small", null, "Mbps", -1))
              ])
            ])
          ]),
          s("p", qe, [
            h(d(t("上次测速", "Last tested")) + " ", 1),
            s("time", {
              datetime: ((j = c.value) == null ? void 0 : j.measuredAt) || void 0
            }, d((M = c.value) != null && M.measuredAt ? m(Q)(c.value.measuredAt, m(i)) : t("尚未测速", "No test yet")), 9, he)
          ])
        ]),
        s("div", we, [
          s("div", {
            "data-tone": x("nat")
          }, [
            a[7] || (a[7] = s("span", null, [
              s("i", { "aria-hidden": "true" }),
              h("NAT")
            ], -1)),
            s("strong", {
              title: L("nat")
            }, d(L("nat")), 9, _e)
          ], 8, ke),
          s("div", {
            "data-tone": x("ipv6")
          }, [
            a[8] || (a[8] = s("span", null, [
              s("i", { "aria-hidden": "true" }),
              h("IPv6")
            ], -1)),
            s("strong", {
              class: V({ "qs-card-warning": R("ipv6") }),
              title: L("ipv6")
            }, d(L("ipv6")), 11, Ne)
          ], 8, Ae)
        ]),
        f.value ? (k(), _("div", Te, [
          s("span", null, [
            h(d(N.value), 1),
            s("small", null, d(t("上次有效结果保持显示", "Previous valid results remain visible")), 1)
          ]),
          s("button", {
            disabled: m(n).cancelling || m(n).task.state === "cancel_requested",
            onClick: a[1] || (a[1] = (H) => m(b).stop())
          }, d(m(n).cancelling || m(n).task.state === "cancel_requested" ? t("正在停止", "Stopping") : t("停止", "Stop")), 9, Se)
        ])) : D("", !0),
        m(n).error ? (k(), _("p", Ce, [
          h(d(T.value) + " ", 1),
          s("button", {
            onClick: a[2] || (a[2] = (H) => m(n).errorAction === "run" ? u() : m(b).reload())
          }, d(m(n).paused ? t("恢复查询", "Resume queries") : t("重试", "Retry")), 1)
        ])) : m(n).summary && m(n).summary.service.state !== "ready" ? (k(), _("p", ze, [
          h(d(m(n).summary.service.state === "disabled" ? t("服务未启用", "Service disabled") : t("服务暂不可用", "Service unavailable")) + " ", 1),
          s("a", { href: o }, d(t("打开设置", "Open settings")), 1)
        ])) : m(n).task && ["failed", "cancelled", "interrupted", "partial"].includes(m(n).task.state) ? (k(), _("p", Fe, [
          h(d(C.value) + " ", 1),
          m(n).task.state === "failed" ? (k(), _("button", {
            key: 0,
            onClick: u
          }, d(t("重试测速", "Retry test")), 1)) : D("", !0)
        ])) : D("", !0),
        (J = m(n).summary) != null && J.service.persistenceError ? (k(), _("p", Pe, d(t("结果保存失败，请检查设备存储", "Result could not be saved; check device storage")), 1)) : D("", !0),
        s("footer", Ee, [
          s("span", null, [
            a[9] || (a[9] = s("span", {
              class: "fn-route-dot",
              "aria-hidden": "true"
            }, null, -1)),
            h(d(m(ie)((G = c.value) == null ? void 0 : G.measuredAt) ? t("结果较早，可重新测速", "Older result; test again") : t("默认外网出口", "Default WAN route")), 1)
          ]),
          a[10] || (a[10] = s("small", null, [
            h("FASTNET "),
            s("span", { "aria-hidden": "true" }, "↗")
          ], -1))
        ])
      ], 10, pe);
    };
  }
};
if (!document.getElementById("fastnet-card-v1-style")) {
  const r = document.createElement("style");
  r.id = "fastnet-card-v1-style", r.textContent = se, document.head.appendChild(r);
}
const Re = 1;
export {
  Re as apiVersion,
  Le as default
};
