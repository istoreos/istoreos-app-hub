package syncapps

import (
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

func TestLoadAppIgnoreList(t *testing.T) {
	path := filepath.Join(t.TempDir(), ".syncapps-ignore")
	contents := "# local exclusions\n\nfoo\nbar # not ready\nfoo\n"
	if err := os.WriteFile(path, []byte(contents), 0o600); err != nil {
		t.Fatal(err)
	}

	got, err := LoadAppIgnoreList(path)
	if err != nil {
		t.Fatal(err)
	}
	want := []string{"foo", "bar"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("LoadAppIgnoreList() = %#v, want %#v", got, want)
	}
}

func TestLoadAppIgnoreListRejectsMultipleIDsPerLine(t *testing.T) {
	path := filepath.Join(t.TempDir(), ".syncapps-ignore")
	if err := os.WriteFile(path, []byte("foo bar\n"), 0o600); err != nil {
		t.Fatal(err)
	}

	_, err := LoadAppIgnoreList(path)
	if err == nil || !strings.Contains(err.Error(), "expected one app ID per line") {
		t.Fatalf("LoadAppIgnoreList() error = %v", err)
	}
}

func TestSelectAppsExcludesIgnoredApps(t *testing.T) {
	cfg := &Config{Apps: map[string]AppMapping{
		"alpha": {},
		"beta":  {},
		"gamma": {},
	}}

	got, ignored, err := selectApps(cfg, nil, []string{"gamma", "alpha", "alpha"})
	if err != nil {
		t.Fatal(err)
	}
	if want := []string{"beta"}; !reflect.DeepEqual(got, want) {
		t.Fatalf("selected apps = %#v, want %#v", got, want)
	}
	if want := []string{"alpha", "gamma"}; !reflect.DeepEqual(ignored, want) {
		t.Fatalf("ignored apps = %#v, want %#v", ignored, want)
	}
}

func TestSelectAppsRejectsUnknownIgnoredApp(t *testing.T) {
	cfg := &Config{Apps: map[string]AppMapping{"alpha": {}}}

	_, _, err := selectApps(cfg, nil, []string{"typo"})
	if err == nil || !strings.Contains(err.Error(), "ignored app not found in config: typo") {
		t.Fatalf("selectApps() error = %v", err)
	}
}
