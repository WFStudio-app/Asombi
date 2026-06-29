// Package db - база установленных пакетов
package db

import (
	"encoding/json"
	"os"

	"github.com/WFStudio-app/Asombi/wizzor/internal/config"
)

type InstalledPackage struct {
	Name        string   `json:"name"`
	Version     string   `json:"version"`
	InstallDir  string   `json:"install_dir"`
	URL         string   `json:"url"`
	Description string   `json:"description"`
	Depends     []string `json:"depends"`
}

type InstalledDB map[string]InstalledPackage

func Load() (InstalledDB, error) {
	data, err := os.ReadFile(config.InstalledDB)
	if os.IsNotExist(err) {
		return make(InstalledDB), nil
	}
	if err != nil {
		return nil, err
	}
	var db InstalledDB
	if err := json.Unmarshal(data, &db); err != nil {
		return nil, err
	}
	return db, nil
}

func Save(db InstalledDB) error {
	if err := config.EnsureDirs(); err != nil {
		return err
	}
	data, err := json.MarshalIndent(db, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(config.InstalledDB, data, 0644)
}
