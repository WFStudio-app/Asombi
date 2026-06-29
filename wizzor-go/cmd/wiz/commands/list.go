package commands

import (
	"fmt"
	"sort"

	"github.com/WFStudio-app/Asombi/wizzor/internal/db"
	"github.com/WFStudio-app/Asombi/wizzor/internal/output"
)

func List(args []string) {
	installed, err := db.Load()
	if err != nil {
		output.Err(fmt.Sprintf("Failed to load DB: %s", err))
		return
	}

	if len(installed) == 0 {
		output.Info("No packages installed.")
		return
	}

	// Сортируем по имени
	names := make([]string, 0, len(installed))
	for name := range installed {
		names = append(names, name)
	}
	sort.Strings(names)

	fmt.Printf("\n  %s (%d):\n\n",
		output.Bold("Installed packages"),
		len(installed))

	for _, name := range names {
		pkg := installed[name]
		fmt.Printf("  %-30s v%s\n",
			output.Cyan(name),
			pkg.Version)
		if pkg.Description != "" {
			fmt.Printf("  %-30s %s\n", "", pkg.Description)
		}
	}
	fmt.Println()
}
