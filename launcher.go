package main

import (
	"os"
	"os/exec"
	"path/filepath"
)

// Launches pythonw.exe (no console window) with main.py from the same directory.
// The working directory is set to the exe's own directory so relative imports work.
func main() {
	exe, _ := os.Executable()
	dir := filepath.Dir(exe)
	python := filepath.Join(dir, "python", "pythonw.exe")
	script := filepath.Join(dir, "main.py")
	cmd := exec.Command(python, script)
	cmd.Dir = dir
	_ = cmd.Start()
}
