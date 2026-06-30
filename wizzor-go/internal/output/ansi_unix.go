//go:build !windows

package output

// enableWindowsANSI — на Unix-системах ANSI работает из коробки, ничего делать не нужно.
func enableWindowsANSI() bool {
	return true
}
