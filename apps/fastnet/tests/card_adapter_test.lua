-- Run with the device's own Lua/jsonc; all I/O and authentication inputs are fixtures.
local model=assert(loadfile(arg[1]))()
local json=require "luci.jsonc"
local checks=0
local function run(action,options)
 options=options or {}
 local output={calls=0,headers={}}
 local env={REQUEST_METHOD=(action=="run" or action=="cancel") and "POST" or "GET",CONTENT_TYPE="application/json",HTTP_HOST="router.invalid",HTTP_X_CSRF_TOKEN="fixture-csrf"}
 for k,v in pairs(options.env or {}) do env[k]=v end
 if options.omit_header then env.HTTP_X_CSRF_TOKEN=nil end
 local http={getenv=function(k)return env[k]end,formvalue=function(name)if name=="token" then return options.query_token end;return options.id or "run-example"end,content=function()return options.body or '{"idempotencyKey":"fixture-key-0001"}'end,status=function(s)output.status=s end,prepare_content=function()end,header=function(k,v)output.headers[k]=v end,write=function(value)output.raw=value;output.value=json.parse(value)end}
 local ctx=options.ctx or {authsession="fixture-session",authuser="root",authtoken="fixture-csrf"}
 local deps={http=http,ctx=ctx,json=json,fs={access=function(path)return not options.missing or not path:find(options.missing,1,true)end},enabled=function()return not options.disabled end,state=function()return options.state end,request=function(method,path,body)
  output.calls=output.calls+1;output.method=method;output.path=path;output.body=body
  if options.unavailable then return nil,nil,options.unavailable end
  return options.status or 200,options.response or '{"schemaVersion":1,"instanceId":"fixture","service":{"state":"ready"},"latest":null,"task":null}'
 end}
 model.new(deps):handle(action);checks=checks+1
 return output
end
local function denied(action,options,status)
 local r=run(action,options);assert(r.status==status,r.raw);assert(r.calls==0,"denied request reached core");return r
end
denied("summary",{ctx={}},401)
denied("summary",{ctx={authsession="fixture-session",authuser="reader"}},403)
denied("run",{env={REQUEST_METHOD="GET"}},405)
denied("run",{env={HTTP_X_CSRF_TOKEN="wrong"}},403)
denied("run",{ctx={authsession="fixture-session",authuser="root"}},403)
denied("run",{env={HTTP_ORIGIN="https://other.invalid"}},403)
denied("run",{env={HTTP_SEC_FETCH_SITE="cross-site"}},403)
denied("run",{env={CONTENT_LENGTH="100000"}},413)
for _,body in ipairs({'{}','{"idempotencyKey":"short"}','{"idempotencyKey":"fixture-key-0001","extra":1}','{"idempotencyKey":"fixture-key-0001","idempotencyKey":"fixture-key-0002"}'})do denied("run",{body=body},422)end
denied("task",{id="../run"},422)
denied("summary",{missing="/etc/config"},503)
denied("summary",{missing="/usr/sbin"},503)
local summary=run("summary");assert(summary.status==200 and summary.raw:find('"latest":null',1,true) and summary.raw:find('"task":null',1,true));assert(summary.calls==1);assert(summary.headers['Cache-Control']=="no-store")
local task='{"id":"run-example","state":"running","instanceId":"fixture","error":null}'
local submitted=run("run",{status=202,response=task});assert(submitted.status==202 and submitted.path=="run" and submitted.raw==task);assert(not submitted.body:find("fixture-csrf",1,true))
local query_csrf=run("run",{omit_header=true,query_token="fixture-csrf",status=202,response=task});assert(query_csrf.status==202)
denied("run",{omit_header=true,query_token="wrong"},403)
local queried=run("task",{response=task});assert(queried.path=="task?id=run-example")
local stopped=run("cancel",{body='{"id":"run-example"}',response=task});assert(stopped.status==200 and stopped.path=="cancel")
local bad=run("summary",{response="<html>invalid</html>"});assert(bad.status==502)
local timeout=run("summary",{unavailable="upstream_timeout"});assert(timeout.status==502)
local disabled=run("summary",{disabled=true,unavailable="service_unavailable"});assert(disabled.status==200 and disabled.value.service.state=="disabled");assert(disabled.raw:find('"latest":null',1,true))
local state='{"schemaVersion":1,"jobs":[],"latest":{"runId":"old-run","measuredAt":"2026-11-09T00:00:00Z","download":{"status":"ok","value":0,"measuredAt":"2026-11-09T00:00:00Z","error":null},"upload":{"status":"not_tested","value":null,"measuredAt":null,"error":null},"nat":{"status":"not_tested","value":null,"measuredAt":null,"error":null},"ipv6":{"status":"unavailable","value":null,"measuredAt":"2026-11-09T00:00:00Z","error":null}}}'
local old=run("summary",{state=state,unavailable="service_unavailable"});assert(old.status==200 and old.value.latest.download.value==0 and old.value.service.state=="unavailable");assert(old.raw:find('"value":null',1,true))
print(json.stringify({status="passed",checks=checks}))
