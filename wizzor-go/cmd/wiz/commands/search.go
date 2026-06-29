package commands

import (
	"fmt"
	"strings"

	"github.com/WFStudio-app/Asombi/wizzor/internal/db"
	"github.com/WFStudio-app/Asombi/wizzor/internal/fetch"
	"github.com/WFStudio-app/Asombi/wizzor/internal/output"
	"github.com/WFStudio-app/Asombi/wizzor/internal/repo"
	"github.com/WFStudio-app/Asombi/wizzor/internal/sources"
)

func Search(args []string) {
	if len(args) == 0 {
		output.Err("Usage: wiz search <query>")
		return
	}

	query := strings.ToLower(strings.Join(args, " "))
	installed, _ := db.Load()
	urls := sources.Load()

	allPkgs := make(map[string]repo.Package)

	for _, url := range urls {
		output.Info(fmt.Sprintf("Fetching: %s", url))
		content, err := fetch.Text(url)
		if err != nil {
			output.Warn(fmt.Sprintf("Skipping %s: %s", url, err))
			continue
		}
		idx, err := repo.ParseIndex(content)
		if err != nil {
			output.Warn(fmt.Sprintf("Parse error: %s", err))
			continue
		}
		for name, pkg := range idx.Packages {
			allPkgs[name] = pkg
		}
	}

	// Поиск по имени и описанию
	var found []repo.Package
	for _, pkg := range allPkgs {
		if strings.Contains(strings.ToLower(pkg.Name), query) ||
			strings.Contains(strings.ToLower(pkg.Description), query) {
			found = append(found, pkg)
		}
	}

	if len(found) == 0 {
		output.Warn(fmt.Sprintf("No packages found for '%s'", query))
		return
	}

	fmt.Printf("\n  %s %s\n\n",
		output.Bold("Search results for:"),
		output.Cyan(query))

	for _, pkg := range found {
		status := ""
		if _, ok := installed[pkg.Name]; ok {
			status = output.Green(" [installed]")
		}
		fmt.Printf("  %s v%s%s\n", output.Bold(pkg.Name), pkg.Version, status)
		fmt.Printf("    %s\n\n", pkg.Description)
	}
}
