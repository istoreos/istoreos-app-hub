#!/bin/sh
case "${1:-}" in
 status)
  if pidof optimemachine_bin >/dev/null; then running=true; else running=false; fi
  printf '{"app":"optimemachine","docker":false,"deployed":true,"running":%s,"href":"/cgi-bin/luci/admin/system/optimemachine"}\n' "$running"
 ;;
 start) /etc/init.d/optimemachine enable && /etc/init.d/optimemachine start ;;
 stop) /etc/init.d/optimemachine stop ;;
 *) exit 1 ;;
esac
