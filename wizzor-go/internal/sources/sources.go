// Package sources - работа со списком репозиториев
package sources

import (
	"bufio"
	"os"
	"strings"

	"github.com/WFStudio-app/Asombi/wizzor/internal/config"
)

var defaults = []string{
	"https://raw.githubusercontent.com/WFStudio-app/Asombi/main/packages/index.toml",
}

func Load() []string {
	f, err := os.Open(config.SourcesFile)
	if err != nil {
		return defaults
	}
	defer f.Close()

	var sources []string
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line != "" && !strings.HasPrefix(line, "#") {
			sources = append(sources, line)
		}
	}
	if len(sources) == 0 {
		return defaults
	}
	return sources
}

func Save(sources []string) error {
	if err := config.EnsureDirs(); err != nil {
		return err
	}
	f, err := os.Create(config.SourcesFile)
	if err != nil {
		return err
	}
	defer f.Close()

	f.WriteString("# Wizzor sources.list\n")
	for _, s := range sources {
		f.WriteString(s + "\n")
	}
	return nil
}
