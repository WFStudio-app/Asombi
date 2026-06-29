package repo

import (
	"fmt"
	"strings"

	"github.com/WFStudio-app/Asombi/wizzor/internal/toml"
)

// ParseIndex парсит TOML индекс репозитория
func ParseIndex(content string) (*Index, error) {
	doc, err := toml.Parse(content)
	if err != nil {
		return nil, fmt.Errorf("parse error: %w", err)
	}

	idx := &Index{
		Packages: make(map[string]Package),
	}

	// Метаданные репо
	idx.Repo = RepoMeta{
		Name:       doc.GetStr("repo", "name"),
		Maintainer: doc.GetStr("repo", "maintainer"),
		Updated:    doc.GetStr("repo", "updated"),
	}

	// Пакеты — секции вида [packages.curl]
	for _, section := range doc.Sections("packages.") {
		name := strings.TrimPrefix(section, "packages.")
		if name == "" {
			continue
		}

		pkg := Package{
			Name:        name,
			Version:     doc.GetStr(section, "version"),
			Description: doc.GetStr(section, "description"),
			URL:         doc.GetStr(section, "url"),
			SHA256:      doc.GetStr(section, "sha256"),
			Size:        doc.GetStr(section, "size"),
			License:     doc.GetStr(section, "license"),
			PostInstall: doc.GetStr(section, "post_install"),
			Depends:     doc.GetArr(section, "depends"),
		}
		idx.Packages[name] = pkg
	}

	return idx, nil
}
