local ctx={authsession='fixture',authuser='root'}
local env,result
package.loaded['luci.dispatcher']={context=ctx}
package.loaded['luci.http']={getenv=function(k)return env[k]end,status=function(s)result.status=s end,prepare_content=function()end,header=function(k,v)result[k]=v end,write_json=function(v)result.value=v end}
package.loaded['nixio']={getifaddrs=function()return {{addr='127.0.0.1'},{addr='192.168.30.7'},{addr='fd00::7'}}end}
assert(loadfile(arg[1]))()
local checks=0
local function run(address,options)
 options=options or {};env={REMOTE_ADDR=address,REQUEST_METHOD=options.method or 'GET',HTTP_X_FORWARDED_FOR='127.0.0.1'};result={};ctx.authuser=options.user or 'root';ctx.authsession='fixture';if options.anonymous then ctx.authsession=nil end
 luci.controller.fastnet.action_browser_origin();checks=checks+1;return result
end
assert(run('192.168.30.19',{anonymous=true}).status==403)
assert(run('192.168.30.19',{user='reader'}).status==403)
assert(run('192.168.30.19',{method='POST'}).status==405)
assert(run(nil).status==503)
assert(run('invalid/ip').status==503)
for _,address in ipairs({'127.0.0.1','::1','::ffff:127.0.0.1'}) do local r=run(address);assert(r.value.isLoopback and r.value.isLocal) end
for _,address in ipairs({'192.168.30.19','fd00::19'}) do local r=run(address);assert(not r.value.isLoopback and not r.value.isLocal);assert(r['Cache-Control']=='no-store');assert(r.value.clientIP==nil) end
for _,address in ipairs({'192.168.30.7','fd00::7'}) do local r=run(address);assert(not r.value.isLoopback and r.value.isLocal) end
print('browser origin adapter checks passed: '..checks)
