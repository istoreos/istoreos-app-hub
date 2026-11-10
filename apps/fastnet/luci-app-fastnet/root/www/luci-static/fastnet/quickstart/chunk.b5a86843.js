import { ref as l, computed as B, watch as I, onMounted as L, onUnmounted as O, openBlock as f, createElementBlock as p, createElementVNode as o, createTextVNode as V, toDisplayString as i, createCommentVNode as u } from "/luci-static/quickstart/card-runtime-v1.js";
const j = ".fn-web-dialog{width:100%;min-width:0;min-height:0;display:flex;flex-direction:column;background:var(--qs-card-panel);color:var(--qs-card-text)}.fn-web-toolbar{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px;padding:10px 20px;border-bottom:1px solid var(--qs-card-line);font-size:11px;letter-spacing:1px}.fn-web-toolbar small{letter-spacing:0;color:var(--qs-card-muted)}.fn-web-toolbar a{color:var(--qs-card-accent);letter-spacing:0;padding:4px}.fn-web-frame{position:relative;flex:1;min-height:0}.fn-web-frame iframe{display:block;border:0;width:100%;height:100%;background:var(--qs-card-panel)}.fn-web-loading{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:24px;text-align:center;background:var(--qs-card-panel);color:var(--qs-card-muted)}.fn-web-loading strong{color:var(--qs-card-text);font-size:16px}.fn-web-loading p{font-size:12px;line-height:1.7;max-width:360px;margin:0}.fn-web-loading button{font:inherit;color:var(--qs-card-accent);border:1px solid var(--qs-card-line);background:var(--qs-card-soft);padding:10px 20px;border-radius:8px;cursor:pointer}.fn-web-footnote{font-size:10px;color:var(--qs-card-muted);line-height:1.6;margin:0!important;padding:9px 20px;border-top:1px solid var(--qs-card-line)}@media(max-width:600px){.fn-web-toolbar{padding:8px 14px}.fn-web-toolbar small{display:none}.fn-web-footnote{padding:8px 14px}}", D = {
  class: "fn-web-dialog",
  "data-fastnet-web-dialog": ""
}, M = { class: "fn-web-toolbar" }, P = {
  href: "/cgi-bin/luci/admin/services/fastnet/open",
  target: "_blank",
  rel: "noopener"
}, R = { class: "fn-web-frame" }, U = ["src", "title"], G = ["role"], H = { class: "fn-web-footnote" }, K = {
  __name: "WebDialog",
  props: ["context", "locale", "view"],
  emits: ["close"],
  setup(S, { emit: A }) {
    if (!document.getElementById("fastnet-web-v1-style")) {
      const e = document.createElement("style");
      e.id = "fastnet-web-v1-style", e.textContent = j, document.head.appendChild(e);
    }
    const s = S, E = A, a = (e, t) => s.locale === "en" ? t : e, r = l(null), c = l(!1), n = l(!1), m = l(0), F = B(() => "/cgi-bin/luci/admin/services/fastnet/embed?theme=" + s.context.theme.effective + (s.view === "history" ? "&view=history" : ""));
    let d;
    function g() {
      clearTimeout(d), d = setTimeout(() => {
        c.value || (n.value = !0);
      }, 15e3);
    }
    function C() {
      c.value = !1, n.value = !1, m.value++, g();
    }
    function w() {
      var e, t;
      (t = (e = r.value) == null ? void 0 : e.contentWindow) == null || t.postMessage({ type: "quickstart:theme", theme: s.context.theme.effective }, location.origin);
    }
    function b(e) {
      var t, v, x, h, y, _, k, q, N, T;
      e.origin !== location.origin || e.source !== ((t = r.value) == null ? void 0 : t.contentWindow) || (((v = e.data) == null ? void 0 : v.type) === "fastnet:ready" ? (clearTimeout(d), c.value = !0, n.value = !1, w()) : ((x = e.data) == null ? void 0 : x.type) === "fastnet:close" ? E("close") : ((h = e.data) == null ? void 0 : h.type) === "fastnet:focus" && (e.data.backward ? (k = (_ = (y = r.value) == null ? void 0 : y.closest(".fn-web-dialog")) == null ? void 0 : _.querySelector("a")) == null || k.focus() : (T = (N = (q = r.value) == null ? void 0 : q.closest("section.network-dialog")) == null ? void 0 : N.querySelector("[data-network-dialog-close]")) == null || T.focus()));
    }
    const W = F.value, z = l(W);
    return I(() => s.context.theme.effective, w), L(() => {
      window.addEventListener("message", b), g();
    }), O(() => {
      clearTimeout(d), window.removeEventListener("message", b);
    }), (e, t) => (f(), p("div", D, [
      o("div", M, [
        o("span", null, [
          t[0] || (t[0] = V("FASTNET ", -1)),
          o("small", null, "· " + i(a("WAN / LAN / NAT / IPv6", "WAN speed / NAT / IPv6")), 1)
        ]),
        o("a", P, i(a("新窗口打开", "Open in new window")) + " ↗", 1)
      ]),
      o("div", R, [
        n.value ? u("", !0) : (f(), p("iframe", {
          key: m.value,
          ref_key: "frame",
          ref: r,
          src: z.value,
          title: a("FastNet 完整测速界面", "FastNet speed test interface"),
          referrerpolicy: "same-origin"
        }, null, 8, U)),
        c.value ? u("", !0) : (f(), p("div", {
          key: 1,
          class: "fn-web-loading",
          role: n.value ? "alert" : "status"
        }, [
          o("strong", null, i(n.value ? a("FastNet 页面暂时无法加载", "FastNet could not be loaded") : a("正在打开 FastNet…", "Opening FastNet…")), 1),
          o("p", null, i(n.value ? a("可以重试，或在新窗口中打开。请确认插件服务已启用。", "Retry or open in a new window. Check that the plugin service is enabled.") : a("打开页面不会自动测速；请在子窗口中点击开始。", "Opening the page does not start a test. Select Start inside the window.")), 1),
          n.value ? (f(), p("button", {
            key: 0,
            onClick: C
          }, i(a("重新加载", "Reload")), 1)) : u("", !0)
        ], 8, G))
      ]),
      o("p", H, i(a("核心已接受的测速继续运行；关闭窗口将中断浏览器测量，已保存结果保留。", "Accepted core tests continue. Browser tests stop when closed; saved results remain.")), 1)
    ]));
  }
};
export {
  K as default
};
