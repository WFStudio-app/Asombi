//go:build windows

package output

import (
	"syscall"
	"unsafe"
)

const enableVirtualTerminalProcessing = 0x0004

// enableWindowsANSI включает поддержку ANSI escape-кодов в Windows Terminal / cmd.exe (Windows 10+)
func enableWindowsANSI() bool {
	kernel32 := syscall.NewLazyDLL("kernel32.dll")
	getStdHandle := kernel32.NewProc("GetStdHandle")
	getConsoleMode := kernel32.NewProc("GetConsoleMode")
	setConsoleMode := kernel32.NewProc("SetConsoleMode")

	const stdOutputHandle = ^uintptr(10) + 1 // -11

	handle, _, _ := getStdHandle.Call(uintptr(0xFFFFFFF5)) // STD_OUTPUT_HANDLE = -11
	if handle == 0 {
		return false
	}

	var mode uint32
	ret, _, _ := getConsoleMode.Call(handle, uintptr(unsafe.Pointer(&mode)))
	if ret == 0 {
		return false
	}

	mode |= enableVirtualTerminalProcessing
	ret, _, _ = setConsoleMode.Call(handle, uintptr(mode))
	return ret != 0
}
