-- Pure fixtures, run under the appliance's Lua. Never opens a session or a test.
local ctx, method, decision, preference, result
local http={getenv=function()return method end,formvalue=function()return preference end,status=function(v)result.status=v end,prepare_content=function()end,write=function(v)result.body=v end,header=function(k,v)result[k]=v end,urlencode=function(v)return v end,redirect=function(v)result.redirect=v end}
package.loaded['luci.http']=http
package.loaded['luci.dispatcher']={context={},build_url=function(...)return '/'..table.concat({...},'/')end}
package.loaded['luci.model.linkease.apps_openwrt']={new=function()return {resolve=function()return decision end}end}
assert(loadfile(arg[1]))()
local checks=0
local function run(options)
 options=options or {};result={};method=options.method or 'GET';preference=options.theme
 ctx=package.loaded['luci.dispatcher'].context;ctx.authsession='fixture';if options.session==false then ctx.authsession=nil end;ctx.authuser=options.user or 'root'
 decision=options.decision or {available=true,url='/apps/fastnet/'}
 luci.controller.fastnet.action_embed();checks=checks+1;return result
end
assert(run({method='POST'}).status==405)
assert(run({user='reader'}).status==403)
assert(run({session=false}).status==403)
assert(run({decision={available=false,url='/apps/fastnet/'}}).status==503)
assert(run({decision={available=true,url='http://router.invalid:3200/'}}).status==503)
assert(run({decision={available=true,url='//foreign.invalid/'}}).status==503)
assert(run({decision={available=true}}).status==503)
local valid=run({theme='dark'});assert(valid.redirect=='/admin/services/linkease_auth/auth?return=/apps/fastnet/?embed=quickstart&theme=dark');assert(valid['Cache-Control']=='no-store')
assert(run({theme='javascript:invalid'}).redirect:find('theme=light',1,true))
assert(run({decision={available=true,url='/apps/fastnet/?known=1'}}).redirect:find('?known=1&embed=quickstart',1,true))
print('embed controller checks passed: '..checks)
