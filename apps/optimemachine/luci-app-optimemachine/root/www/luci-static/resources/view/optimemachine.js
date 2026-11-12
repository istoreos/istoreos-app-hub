'use strict';
'require view';
'require uci';
return view.extend({load:function(){return uci.load('optimemachine');},render:function(){return E('div',{class:'cbi-map'},[E('h2',{},'时光机'),E('p',{},'独立备份、历史文件浏览与设备失联恢复。可在管理界面设置备份位置、查看保护任务、差异与恢复日志。'),E('p',{},'运行配置：'+(uci.get('optimemachine','main','config_file')||'/etc/optimemachine/config.json')),E('a',{class:'cbi-button cbi-button-action',href:'/cgi-bin/luci/admin/services/linkease_apps/open?id=optimemachine',target:'_blank',rel:'noopener'},'打开时光机')]);},handleSaveApply:null,handleSave:null,handleReset:null});
