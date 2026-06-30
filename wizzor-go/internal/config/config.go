package config

import (
	"os"
	"path/filepath"
	"runtime"
)

// HomeDir определяет домашнюю директорию кросс-платформенно.
// На Windows используем USERPROFILE, на Unix-системах HOME.
func homeDir() string {
	if runtime.GOOS == "windows" {
		if h := os.Getenv("USERPROFILE"); h != "" {
			return h
		}
		// Fallback: склеиваем HOMEDRIVE + HOMEPATH
		drive := os.Getenv("HOMEDRIVE")
		path := os.Getenv("HOMEPATH")
		if drive != "" && path != "" {
			return drive + path
		}
	}
	if h := os.Getenv("HOME"); h != "" {
		return h
	}
	// Termux fallback
	if h := os.Getenv("PREFIX"); h != "" {
		return filepath.Join(h, "..", "home")
	}
	h, err := os.UserHomeDir()
	if err == nil {
		return h
	}
	return "."
}

var (
	HomeDir     = homeDir()
	WizDir      = filepath.Join(HomeDir, ".wizzor")
	InstalledDB = filepath.Join(WizDir, "installed.json")
	CacheDir    = filepath.Join(WizDir, "cache")
	SourcesFile = filepath.Join(WizDir, "sources.list")
	PackagesDir = filepath.Join(WizDir, "packages")
)

var DefaultRepos = []string{
	"https://raw.githubusercontent.com/WFStudio-app/Asombi/main/packages/index.toml",
}

// IsWindows сообщает, запущены ли мы на Windows
func IsWindows() bool {
	return runtime.GOOS == "windows"
}

// EnsureDirs создаёт нужные папки если их нет.
// Использует os.ModePerm-совместимые права, безопасные и на Windows, и на Unix.
func EnsureDirs() error {
	dirs := []string{WizDir, CacheDir, PackagesDir}
	for _, d := range dirs {
		if err := os.MkdirAll(d, 0755); err != nil {
			return err
		}
	}
	return nil
}
