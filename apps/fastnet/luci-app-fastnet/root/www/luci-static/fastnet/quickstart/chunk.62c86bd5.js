import { ref as i, computed as V, watch as B, onMounted as D, onUnmounted as I, openBlock as d, createElementBlock as f, createElementVNode as n, createTextVNode as L, toDisplayString as s, createCommentVNode as m } from "/luci-static/quickstart/card-runtime-v1.js";
const M = {
  class: "fn-web-dialog",
  "data-fastnet-web-dialog": ""
}, P = { class: "fn-web-toolbar" }, R = {
  href: "/cgi-bin/luci/admin/services/fastnet/open",
  target: "_blank",
  rel: "noopener"
}, U = { class: "fn-web-frame" }, j = ["src", "title"], z = ["role"], G = { class: "fn-web-footnote" }, J = {
  __name: "WebDialog",
  props: ["context", "locale"],
  emits: ["close"],
  setup(F, { emit: A }) {
    const r = F, E = A, o = (e, t) => r.locale === "en" ? t : e, l = i(null), c = i(!1), a = i(!1), p = i(0), W = V(() => "/cgi-bin/luci/admin/services/fastnet/embed?theme=" + r.context.theme.effective);
    let u;
    function v() {
      clearTimeout(u), u = setTimeout(() => {
        c.value || (a.value = !0);
      }, 15e3);
    }
    function C() {
      c.value = !1, a.value = !1, p.value++, v();
    }
    function g() {
      var e, t;
      (t = (e = l.value) == null ? void 0 : e.contentWindow) == null || t.postMessage({ type: "quickstart:theme", theme: r.context.theme.effective }, location.origin);
    }
    function w(e) {
      var t, h, _, b, y, k, N, T, S, x;
      e.origin !== location.origin || e.source !== ((t = l.value) == null ? void 0 : t.contentWindow) || (((h = e.data) == null ? void 0 : h.type) === "fastnet:ready" ? (clearTimeout(u), c.value = !0, a.value = !1, g()) : ((_ = e.data) == null ? void 0 : _.type) === "fastnet:close" ? E("close") : ((b = e.data) == null ? void 0 : b.type) === "fastnet:focus" && (e.data.backward ? (N = (k = (y = l.value) == null ? void 0 : y.closest(".fn-web-dialog")) == null ? void 0 : k.querySelector("a")) == null || N.focus() : (x = (S = (T = l.value) == null ? void 0 : T.closest("section.network-dialog")) == null ? void 0 : S.querySelector("[data-network-dialog-close]")) == null || x.focus()));
    }
    const q = W.value, O = i(q);
    return B(() => r.context.theme.effective, g), D(() => {
      window.addEventListener("message", w), v();
    }), I(() => {
      clearTimeout(u), window.removeEventListener("message", w);
    }), (e, t) => (d(), f("div", M, [
      n("div", P, [
        n("span", null, [
          t[0] || (t[0] = L("FASTNET ", -1)),
          n("small", null, "· " + s(o("外网速率 / NAT / IPv6", "WAN speed / NAT / IPv6")), 1)
        ]),
        n("a", R, s(o("新窗口打开", "Open in new window")) + " ↗", 1)
      ]),
      n("div", U, [
        a.value ? m("", !0) : (d(), f("iframe", {
          key: p.value,
          ref_key: "frame",
          ref: l,
          src: O.value,
          title: o("FastNet 完整测速界面", "FastNet speed test interface"),
          referrerpolicy: "same-origin"
        }, null, 8, j)),
        c.value ? m("", !0) : (d(), f("div", {
          key: 1,
          class: "fn-web-loading",
          role: a.value ? "alert" : "status"
        }, [
          n("strong", null, s(a.value ? o("FastNet 页面暂时无法加载", "FastNet could not be loaded") : o("正在打开 FastNet…", "Opening FastNet…")), 1),
          n("p", null, s(a.value ? o("可以重试，或在新窗口中打开。请确认插件服务已启用。", "Retry or open in a new window. Check that the plugin service is enabled.") : o("打开页面不会自动测速；请在子窗口中点击开始。", "Opening the page does not start a test. Select Start inside the window.")), 1),
          a.value ? (d(), f("button", {
            key: 0,
            onClick: C
          }, s(o("重新加载", "Reload")), 1)) : m("", !0)
        ], 8, z))
      ]),
      n("p", G, s(o("关闭窗口不会停止已提交的外网测速；结果将同步回首页卡片。", "Closing this window keeps a submitted WAN test running; results return to the homepage card.")), 1)
    ]));
  }
};
export {
  J as default
};
