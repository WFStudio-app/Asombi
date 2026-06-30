package output

import (
	"fmt"
	"os"
	"runtime"
)

var (
	green  = "\033[92m"
	red    = "\033[91m"
	yellow = "\033[93m"
	cyan   = "\033[96m"
	bold   = "\033[1m"
	reset  = "\033[0m"
)

func init() {
	if runtime.GOOS == "windows" && !enableWindowsANSI() {
		// Если не удалось включить ANSI (старый cmd.exe) — работаем без цвета
		green, red, yellow, cyan, bold, reset = "", "", "", "", "", ""
	}
}

func Ok(msg string)   { fmt.Printf("  %s[OK]%s %s\n", green, reset, msg) }
func Err(msg string)  { fmt.Printf("  %s[ERR]%s %s\n", red, reset, msg) }
func Info(msg string) { fmt.Printf("  %s[i]%s %s\n", cyan, reset, msg) }
func Warn(msg string) { fmt.Printf("  %s[!]%s %s\n", yellow, reset, msg) }

func Bold(msg string) string  { return fmt.Sprintf("%s%s%s", bold, msg, reset) }
func Green(msg string) string { return fmt.Sprintf("%s%s%s", green, msg, reset) }
func Cyan(msg string) string  { return fmt.Sprintf("%s%s%s", cyan, msg, reset) }
func Red(msg string) string   { return fmt.Sprintf("%s%s%s", red, msg, reset) }

// IsTerminal сообщает, пишем ли мы в реальный терминал (а не в файл/пайп)
func IsTerminal() bool {
	fi, err := os.Stdout.Stat()
	if err != nil {
		return false
	}
	return (fi.Mode() & os.ModeCharDevice) != 0
}
