package output

import "fmt"

const (
	green  = "\033[92m"
	red    = "\033[91m"
	yellow = "\033[93m"
	cyan   = "\033[96m"
	bold   = "\033[1m"
	reset  = "\033[0m"
)

func Ok(msg string)   { fmt.Printf("  %s[✓]%s %s\n", green, reset, msg) }
func Err(msg string)  { fmt.Printf("  %s[✗]%s %s\n", red, reset, msg) }
func Info(msg string) { fmt.Printf("  %s[i]%s %s\n", cyan, reset, msg) }
func Warn(msg string) { fmt.Printf("  %s[!]%s %s\n", yellow, reset, msg) }

func Bold(msg string) string  { return fmt.Sprintf("%s%s%s", bold, msg, reset) }
func Green(msg string) string { return fmt.Sprintf("%s%s%s", green, msg, reset) }
func Cyan(msg string) string  { return fmt.Sprintf("%s%s%s", cyan, msg, reset) }
func Red(msg string) string   { return fmt.Sprintf("%s%s%s", red, msg, reset) }
