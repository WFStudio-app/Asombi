// Package repo - типы данных для репозиториев и пакетов
package repo

// Index — полный индекс репозитория
type Index struct {
	Repo     RepoMeta
	Packages map[string]Package
}

// RepoMeta — метаданные репозитория
type RepoMeta struct {
	Name       string
	Maintainer string
	Updated    string
}

// Package — один пакет в репозитории
type Package struct {
	Name        string
	Version     string
	Description string
	URL         string
	SHA256      string
	Size        string
	Depends     []string
	License     string
	PostInstall string
}
