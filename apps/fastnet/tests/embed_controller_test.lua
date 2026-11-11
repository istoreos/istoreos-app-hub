-- Pure fixtures: exercise the real controller without a router session or test.
local ctx, env, form, config, result
local http={getenv=function(k)return env[k] end,formvalue=function(k)return form[k] end,
 status=function(v)result.status=v end,prepare_content=function(v)result.contentType=v end,
 write=function(v)result.body=v end,write_json=function(v)result.json=v end,
 header=function(k,v)result[k]=v end,redirect=function(v)result.redirect=v end,
 urlencode=function(v)return (v:gsub("([^%w%-_%.~])",function(c)return string.format("%%%02X",string.byte(c))end))end}
package.loaded['luci.http']=http
package.loaded['luci.dispatcher']={context={},build_url=function(...)return '/'..table.concat({...},'/')end}
package.loaded['luci.model.uci']={cursor=function()return {get_first=function(_,_,_,key)return config[key] end}end}
assert(loadfile(arg[1]))()
local checks=0
local function run(options)
 options=options or {};result={};env={REQUEST_METHOD=options.method or 'GET',HTTP_HOST=options.host or '192.168.30.7:10000'}
 form={theme=options.theme,view=options.view,format=options.format,standalone=options.standalone}
 config={port=options.port,token=options.token,enabled=options.enabled}
 ctx=package.loaded['luci.dispatcher'].context;ctx.authsession='fixture';if options.session==false then ctx.authsession=nil end;ctx.authuser=options.user or 'root'
 luci.controller.fastnet.action_embed();checks=checks+1;return result
end
assert(run({method='POST'}).status==405)
assert(run({user='reader'}).status==403)
assert(run({session=false}).status==403)
assert(run({enabled='0'}).status==503)
local direct=run({theme='dark',format='json'})
assert(direct.json.url=='http://192.168.30.7:3200/webui/?embed=quickstart&theme=dark','iframe must connect directly to the FastNet port')
assert(direct['Cache-Control']=='no-store')
assert(direct['Referrer-Policy']=='no-referrer')
assert(direct.contentType=='application/json')
assert(not direct.redirect)
assert(run({theme='dark'}).redirect==direct.json.url)
assert(run({host='[fd00::1]:10000',format='json',port='4321'}).json.url=='http://[fd00::1]:4321/webui/?embed=quickstart&theme=light')
assert(run({host='router.local:80',format='json',port='3300'}).json.url:find('http://router.local:3300/',1,true)==1)
for _,host in ipairs({'evil.test/path','user@evil.test','//evil.test','evil.test:bad','evil.test\r\nInjected: value'}) do assert(run({host=host}).status==503) end
for _,port in ipairs({'0','65536','-1','3200.5','bad'}) do assert(run({port=port}).status==503) end
assert(run({theme='javascript:invalid'}).redirect:find('theme=light',1,true))
assert(run({theme='dark',view='history'}).redirect:find('&view=history',1,true))
assert(not run({view='https://evil.test'}).redirect:find('&view=',1,true))
assert(run({standalone='1'}).redirect=='http://192.168.30.7:3200/webui/')
assert(run({token='secret +&'}).redirect:find('token=secret%20%2B%26',1,true))
run();luci.controller.fastnet.action_open();assert(result.redirect=='/admin/services/fastnet/embed?standalone=1')
print('direct embed controller checks passed: '..checks)
