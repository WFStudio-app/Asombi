package config

import (
	"os"
	"path/filepath"
)

// Пути к данным Wizzor
var (
	HomeDir      = os.Getenv("HOME")
	WizDir       = filepath.Join(HomeDir, ".wizzor")
	InstalledDB  = filepath.Join(WizDir, "installed.json")
	CacheDir     = filepath.Join(WizDir, "cache")
	SourcesFile  = filepath.Join(WizDir, "sources.list")
	PackagesDir  = filepath.Join(WizDir, "packages")
)

var DefaultRepos = []string{
	"https://raw.githubusercontent.com/WFStudio-app/Asombi/main/packages/index.json",
}

// EnsureDirs создаёт нужные папки если их нет
func EnsureDirs() error {
	dirs := []string{WizDir, CacheDir, PackagesDir}
	for _, d := range dirs {
		if err := os.MkdirAll(d, 0755); err != nil {
			return err
		}
	}
	return nil
}
