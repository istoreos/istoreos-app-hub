"use strict";
"require view";

// Reuse the device's Auth Bridge. Its HttpOnly /apps cookie is established
// from the existing LuCI session; no SID or password enters JavaScript.
var base = '/apps/optimemachine/';
return view.extend({
 load: async function() {
  var response = await fetch(L.url('admin/services/linkease_auth/auth') +
   '?return=' + encodeURIComponent(base + 'workspace.html'), {credentials:'same-origin',cache:'no-store'});
  if (!response.ok || new URL(response.url).pathname !== base + 'workspace.html')
   throw new Error('设备认证未完成，请重新登录路由器。');
  var html = await response.text();
  if (!window.OptimemachineUI) await new Promise(function(resolve,reject) {
   var script = document.createElement('script');
   script.src = base + 'app.js'; script.onload = resolve;
   script.onerror = function(){reject(new Error('时光机页面资源加载失败，请检查服务状态。'));};
   document.head.appendChild(script);
  });
  return html;
 },
 render: function(html) {
  var host = E('div',{id:'optimemachine-app',class:'cbi-map',style:'padding-top:3rem'});
  var root = host.attachShadow({mode:'open'});
  var parsed = new DOMParser().parseFromString(html,'text/html');
  var main = parsed.querySelector('main[data-optimemachine]');
  if (!main || !window.OptimemachineUI) throw new Error('时光机页面资源不完整。');
  var css = document.createElement('link'); css.rel='stylesheet'; css.href=base+'style.css';
  root.appendChild(css);root.appendChild(document.importNode(main,true));
  window.OptimemachineUI.mount(root,base);
  return host;
 },
 handleSaveApply:null,handleSave:null,handleReset:null
});
