#!/bin/sh

. /lib/functions.sh

normalize_base_path() {
  base="$1"
  [ -n "$base" ] || base="/apps/"
  case "$base" in
    /*) ;;
    *) base="/$base" ;;
  esac
  case "$base" in
    */) ;;
    *) base="$base/" ;;
  esac
  echo "$base"
}

resolve_data_root_parent() {
  parent="`uci -q get linkease.@linkease[0].data_root_parent`"
  if [ -z "$parent" ]; then
    parent="`uci -q get linkease.@linkease[0].local_home`"
  fi
  if [ -z "$parent" ] && [ -f "/etc/config/quickstart" ]; then
    parent="`uci -q get quickstart.main.main_dir`"
  fi
  if [ -z "$parent" ]; then
    parent="/tmp/linkease"
  fi
  echo "$parent"
}

case "$1" in
  save)
    if [ ! -z "$2" ]; then
      uci set "linkease.@linkease[0].preconfig=$2"
      uci commit
    fi
    ;;

  load)
    if [ -f "/usr/sbin/preconfig.data" ]; then
      data="`cat /usr/sbin/preconfig.data`"
      uci set "linkease.@linkease[0].preconfig=${data}"
      uci commit
      rm /usr/sbin/preconfig.data
    else
      data="`uci -q get linkease.@linkease[0].preconfig`"
    fi

    if [ -z "${data}" ]; then
      echo "nil"
    else
      echo "${data}"
    fi

    ;;

  local_save)
    if [ ! -z "$2" ]; then
      uci set "linkease.@linkease[0].local_home=$2"
      uci commit
      ROOT_DIR="$2"
      if [ -f "/etc/config/quickstart" ]; then
        config_load quickstart
        config_get MAIN_DIR main main_dir ""
        config_get CONF_DIR main conf_dir ""
        config_get PUB_DIR main pub_dir ""
        config_get DL_DIR main dl_dir ""
        config_get TMP_DIR main tmp_dir ""
        # echo "$MAIN_DIR $CONF_DIR $PUB_DIR $DL_DIR $TMP_DIR"
        if [ "$ROOT_DIR" = "$MAIN_DIR" ]; then
          exit 0
        fi
        uci set "quickstart.main.main_dir=$ROOT_DIR"
        if [ -z "$CONF_DIR" -o "$CONF_DIR" = "$MAIN_DIR/Configs" ]; then
          uci set "quickstart.main.conf_dir=$ROOT_DIR/Configs"
        fi
        if [ -z "$PUB_DIR" -o "$PUB_DIR" = "$MAIN_DIR/Public" ]; then
          uci set "quickstart.main.pub_dir=$ROOT_DIR/Public"
        fi
        if [ -z "$DL_DIR" -o "$DL_DIR" = "$MAIN_DIR/Public/Downloads" ]; then
          uci set "quickstart.main.dl_dir=$ROOT_DIR/Public/Downloads"
        fi
        if [ -z "$TMP_DIR" -o "$TMP_DIR" = "$MAIN_DIR/Caches" ]; then
          uci set "quickstart.main.tmp_dir=$ROOT_DIR/Caches"
        fi
        uci commit
      fi
    fi
    ;;

  local_load)
    if [ -f "/etc/config/quickstart" ]; then
      data="`uci -q get quickstart.main.main_dir`"
    fi
    if [ -z "$data" ]; then
      data="`uci -q get linkease.@linkease[0].local_home`"
    fi

    if [ -z "${data}" ]; then
      echo "nil"
    else
      echo "${data}"
    fi

    ;;

  desktop_url)
    desktop_port="`uci -q get linkease.@linkease[0].desktop_port`"
    if [ -z "$desktop_port" ]; then
      desktop_port="19290"
    fi
    base="`uci -q get linkease.@linkease[0].desktop_base_path`"
    base="`normalize_base_path "$base"`"
    echo "http://127.0.0.1:${desktop_port}${base}"
    ;;

  data_root)
    parent="`resolve_data_root_parent`"
    echo "${parent}/.linkease_data"
    ;;

  status)
    echo "TODO"
    ;;

  *)
    echo "Usage: $0 {save|load|local_save|local_load|desktop_url|data_root|status}"
    exit 1
esac
