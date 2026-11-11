#!/bin/sh
# Run only with inert fixtures in a disposable root. Never install into /.
set -eu
manager="$1"
task_dir="$2"
case "$task_dir" in /tmp/registration-compatibility.*) ;; *) exit 2 ;; esac
case "$manager" in opkg|apk) ;; *) exit 2 ;; esac

install_fixture() {
    if [ "$manager" = opkg ]; then
        IPKG_INSTROOT="$package_root" opkg -f "$task_dir/opkg.conf" -o "$package_root" --force-postinstall install "$task_dir/fixtures/$1"
    else
        apk --root "$package_root" --no-network --no-cache --force-non-repository --allow-untrusted --repositories-file /dev/null add --initdb "$task_dir/fixtures/$1"
    fi
}

remove_fixture() {
    if [ "$manager" = opkg ]; then
        IPKG_INSTROOT="$package_root" opkg -f "$task_dir/opkg.conf" -o "$package_root" --force-postinstall remove "$1"
    else
        apk --root "$package_root" --no-network --no-cache --allow-untrusted --repositories-file /dev/null del "$1"
    fi
}

check_entries() {
    for directory in linkease/apps.d linkeasefull/desktop-apps.d; do
        [ "$(readlink "$package_root/usr/share/$directory/$filename")" = "$manifest" ]
    done
    [ -f "$package_root$manifest" ]
}

printf 'arch all 100\ndest root /\n' > "$task_dir/opkg.conf"
for app in fastnet ddnsto; do
    owner=fastnet
    filename=17-fastnet.json
    if [ "$app" = ddnsto ]; then owner=luci-app-ddnsto; filename=16-ddnsto.json; fi
    manifest="/usr/share/$app/$app-plugin.json"
    meta="app-meta-$app"
    for order in owner-first meta-first; do
        package_root="$task_dir/roots/$manager-$app-$order"
        mkdir -p "$package_root/var/lock" "$package_root/tmp" "$package_root/usr/lib/opkg/info"
        if [ "$manager" = apk ]; then
            # Scripts run inside this chroot. No --force-no-chroot and no host services.
            mkdir -p "$package_root/bin" "$package_root/lib" "$package_root/tmp" "$package_root/dev"
            cp /bin/busybox "$package_root/bin/busybox"
            cp /lib/libc.so /lib/libgcc_s.so.1 "$package_root/lib/"
            ln -s libc.so "$package_root/lib/ld-musl-x86_64.so.1"
            for tool in sh mkdir ln readlink sha256sum cut rm rmdir; do
                ln -s busybox "$package_root/bin/$tool"
            done
            old=1.0-r1.apk; new=1.0-r2.apk
        else
            old=1.0-1.ipk; new=1.0-2.ipk
        fi
        install_fixture "${owner}_$old"
        install_fixture "${meta}_$old"
        if [ "$order" = owner-first ]; then
            install_fixture "${owner}_$new"
            check_entries
            install_fixture "${meta}_$new"
        else
            install_fixture "${meta}_$new"
            install_fixture "${owner}_$new"
        fi
        check_entries
        # Re-run the exact package repair hook, then exercise uninstall protection.
        if [ "$manager" = opkg ]; then
            IPKG_INSTROOT="$package_root" sh "$package_root/usr/share/$app/register-desktop.sh"
        else
            chroot "$package_root" /bin/sh "/usr/share/$app/register-desktop.sh"
        fi
        check_entries
        legacy="$package_root/usr/share/linkeasefull/desktop-apps.d/$filename"
        if [ "$order" = meta-first ]; then
            rm "$legacy"
            printf '{"custom":true}\n' > "$legacy"
        fi
        remove_fixture "$owner"
        [ ! -L "$package_root/usr/share/linkease/apps.d/$filename" ]
        if [ "$order" = owner-first ]; then
            [ ! -L "$legacy" ] && [ ! -e "$legacy" ]
        else
            [ "$(cat "$legacy")" = '{"custom":true}' ]
        fi
        printf 'PASS %s %s %s install/upgrade/repair/uninstall\n' "$manager" "$app" "$order"
    done
done
