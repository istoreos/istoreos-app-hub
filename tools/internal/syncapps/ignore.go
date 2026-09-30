package syncapps

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

// LoadAppIgnoreList reads one app ID per line. Blank lines, comments, and
// duplicate IDs are ignored. Inline comments start with '#'.
func LoadAppIgnoreList(path string) ([]string, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	seen := make(map[string]bool)
	var apps []string
	scanner := bufio.NewScanner(f)
	for lineNumber := 1; scanner.Scan(); lineNumber++ {
		line := scanner.Text()
		if commentAt := strings.IndexByte(line, '#'); commentAt >= 0 {
			line = line[:commentAt]
		}
		fields := strings.Fields(line)
		if len(fields) == 0 {
			continue
		}
		if len(fields) != 1 {
			return nil, fmt.Errorf("%s:%d: expected one app ID per line", path, lineNumber)
		}
		if !seen[fields[0]] {
			seen[fields[0]] = true
			apps = append(apps, fields[0])
		}
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	return apps, nil
}
