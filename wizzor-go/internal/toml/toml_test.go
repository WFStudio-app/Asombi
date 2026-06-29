package toml

import (
	"testing"
)

var testInput = `
# Test index
[repo]
name = "Asombi Official"
maintainer = "WFWorld"
updated = "2026-06-29"

[packages.curl]
version = "8.0.0"
description = "HTTP transfer tool"
url = "https://example.com/curl.tar.gz"
sha256 = "abc123"
size = "500 KB"
depends = ["openssl"]
license = "MIT"

[packages.git]
version = "2.45.0"
description = "Version control system"
url = "https://example.com/git.tar.gz"
depends = ["curl", "openssl"]
license = "GPL-2.0"
`

func TestParse(t *testing.T) {
	doc, err := Parse(testInput)
	if err != nil {
		t.Fatalf("Parse error: %v", err)
	}

	if doc.GetStr("repo", "name") != "Asombi Official" {
		t.Errorf("repo.name mismatch")
	}

	if doc.GetStr("packages.curl", "version") != "8.0.0" {
		t.Errorf("curl version mismatch")
	}

	deps := doc.GetArr("packages.curl", "depends")
	if len(deps) != 1 || deps[0] != "openssl" {
		t.Errorf("curl depends mismatch: %v", deps)
	}

	sections := doc.Sections("packages.")
	if len(sections) != 2 {
		t.Errorf("expected 2 package sections, got %d", len(sections))
	}
}

func TestEmptyArray(t *testing.T) {
	doc, err := Parse("[pkg.test]\ndepends = []")
	if err != nil {
		t.Fatalf("Parse error: %v", err)
	}
	deps := doc.GetArr("pkg.test", "depends")
	if deps != nil && len(deps) != 0 {
		t.Errorf("expected empty array, got %v", deps)
	}
}
