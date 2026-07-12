#!/bin/sh
set -eu

ensure_section() {
	if ! uci -q get linkease.@linkease[0] >/dev/null; then
		uci -q add linkease linkease >/dev/null
	fi
}

stop_betterapps() {
	if [ -x /etc/init.d/betterapps ]; then
		/etc/init.d/betterapps stop || true
		/etc/init.d/betterapps disable || true
	fi
	rm -f /etc/init.d/betterapps
rm -f /etc/rc.d/S*betterapps
rm -f /etc/rc.d/K*betterapps
}

preserve_local_home_as_data_parent() {
	data_root_parent="$(uci -q get linkease.@linkease[0].data_root_parent || true)"
	if [ -n "$data_root_parent" ]; then
		return 0
	fi

	local_home="$(uci -q get linkease.@linkease[0].local_home || true)"
	if [ -n "$local_home" ]; then
		data_root_parent="$local_home"
	elif [ -f /etc/config/quickstart ]; then
		quickstart_main_dir="$(uci -q get quickstart.main.main_dir || true)"
		if [ -n "$quickstart_main_dir" ]; then
			data_root_parent="$quickstart_main_dir"
		fi
	fi

	if [ -n "${data_root_parent:-}" ]; then
		uci -q set linkease.@linkease[0].data_root_parent="$data_root_parent"
	fi
}

ensure_full_defaults() {
	ensure_section

	enabled="$(uci -q get linkease.@linkease[0].enabled || true)"
	port="$(uci -q get linkease.@linkease[0].port || true)"
	desktop_port="$(uci -q get linkease.@linkease[0].desktop_port || true)"
	desktop_base_path="$(uci -q get linkease.@linkease[0].desktop_base_path || true)"
	desktop_enabled="$(uci -q get linkease.@linkease[0].desktop_enabled || true)"
	apptunnel_enabled="$(uci -q get linkease.@linkease[0].apptunnel_enabled || true)"
	low_memory_fallback="$(uci -q get linkease.@linkease[0].low_memory_fallback || true)"

	[ -n "$enabled" ] || enabled=1
	[ -n "$port" ] || port=8897
	[ -n "$desktop_port" ] || desktop_port=19290
	[ -n "$desktop_base_path" ] || desktop_base_path=/apps/
	[ -n "$desktop_enabled" ] || desktop_enabled=1
	[ -n "$apptunnel_enabled" ] || apptunnel_enabled=1
	[ -n "$low_memory_fallback" ] || low_memory_fallback=1

	uci -q set linkease.@linkease[0].edition='full'
	uci -q set linkease.@linkease[0].enabled="$enabled"
	uci -q set linkease.@linkease[0].port="$port"
	uci -q set linkease.@linkease[0].desktop_port="$desktop_port"
	uci -q set linkease.@linkease[0].desktop_base_path="$desktop_base_path"
	uci -q set linkease.@linkease[0].desktop_enabled="$desktop_enabled"
	uci -q set linkease.@linkease[0].apptunnel_enabled="$apptunnel_enabled"
	uci -q set linkease.@linkease[0].low_memory_fallback="$low_memory_fallback"
}

stop_betterapps
ensure_full_defaults
preserve_local_home_as_data_parent
uci -q commit linkease
