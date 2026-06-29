package main

import (
	"fmt"
	"os"

	"github.com/WFStudio-app/Asombi/wizzor/cmd/wiz/commands"
	"github.com/WFStudio-app/Asombi/wizzor/internal/output"
)

const Version = "0.1.00"

var banner = `
  ██╗    ██╗██╗███████╗███████╗ ██████╗ ██████╗
  ██║    ██║██║╚══███╔╝╚══███╔╝██╔═══██╗██╔══██╗
  ██║ █╗ ██║██║  ███╔╝   ███╔╝ ██║   ██║██████╔╝
  ██║███╗██║██║ ███╔╝   ███╔╝  ██║   ██║██╔══██╗
  ╚███╔███╔╝██║███████╗███████╗╚██████╔╝██║  ██║
   ╚══╝╚══╝ ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝`

var help = `
  Usage:
    wiz <command> [args]

  Package management:
    wiz install <pkg>       Install a package
    wiz remove  <pkg>       Remove a package
    wiz update  [pkg]       Update package(s)
    wiz search  <query>     Search packages
    wiz list                List installed packages
    wiz info    <pkg>       Show package info

  Repository:
    wiz repo list           List repositories
    wiz repo add  <url>     Add a repository
    wiz repo remove <url>   Remove a repository

  Other:
    wiz clean               Clear download cache
    wiz version             Show version
    wiz help                Show this help
`

func main() {
	args := os.Args[1:]

	if len(args) == 0 {
		fmt.Println(banner)
		fmt.Printf("  Wizzor Package Manager v%s | Asombi OS\n", Version)
		fmt.Println(help)
		return
	}

	cmd := args[0]
	rest := args[1:]

	switch cmd {
	case "version", "--version", "-v":
		fmt.Printf("  Wizzor v%s\n", Version)
		fmt.Println("  Asombi OS | ARM64/Android | Go")

	case "help", "--help", "-h":
		fmt.Println(banner)
		fmt.Printf("  Wizzor Package Manager v%s | Asombi OS\n", Version)
		fmt.Println(help)

	case "search":
		commands.Search(rest)

	case "list":
		commands.List(rest)

	default:
		output.Err(fmt.Sprintf("Unknown command: '%s'", cmd))
		fmt.Println("  Run 'wiz help' for usage.")
		os.Exit(1)
	}
}
