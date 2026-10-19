// Validate the actual Docker inspect Go templates without requiring a daemon.
package main

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"text/template"
)

func main() {
	files, err := filepath.Glob("apps/*/luci-app-*/root/usr/libexec/istorec/*.sh")
	if err != nil { panic(err) }
	pattern := regexp.MustCompile(`bindings=\$\(docker inspect --format '([^']+)' ([a-z0-9]+)\)`)
	portPattern := regexp.MustCompile(`"([0-9]+/tcp)"`)
	checked := 0
	for _, file := range files {
		body, err := os.ReadFile(file)
		if err != nil { panic(err) }
		match := pattern.FindSubmatch(body)
		if match == nil { continue }
		port := portPattern.FindSubmatch(match[1])
		if port == nil { panic("missing exact internal port: " + file) }
		tmpl, err := template.New(file).Parse(string(match[1]))
		if err != nil { panic(err) }
		for _, empty := range []bool{false, true} {
			ports := map[string]interface{}{}
			if !empty {
				ports[string(port[1])] = []map[string]string{
					{"HostIp": "0.0.0.0", "HostPort": "43210"},
					{"HostIp": "::", "HostPort": "43210"},
				}
			}
			input := map[string]interface{}{"NetworkSettings": map[string]interface{}{"Ports": ports}}
			var output bytes.Buffer
			if err := tmpl.Execute(&output, input); err != nil { panic(err) }
			expected := "0.0.0.0 43210\n:: 43210\n"
			if empty { expected = "" }
			if output.String() != expected { panic("wrong binding row delimiter: " + file) }
		}
		checked++
	}
	if checked != 9 { panic(fmt.Sprintf("expected 9 templates, checked %d", checked)) }
	fmt.Printf("passed: %d real Docker templates, populated and absent bindings\n", checked)
}
