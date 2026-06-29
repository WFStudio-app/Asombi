// Package toml - минимальный TOML парсер для Wizzor
// Поддерживает: [section], [section.sub], key = "value", arrays
package toml

import (
	"bufio"
	"fmt"
	"strings"
)

// Value хранит любое значение из TOML
type Value struct {
	Str    string
	Array  []string
	IsArr  bool
}

// Document — распарсенный TOML файл
type Document map[string]map[string]Value

// Parse парсит TOML строку в Document
func Parse(input string) (Document, error) {
	doc := make(Document)
	currentSection := ""

	scanner := bufio.NewScanner(strings.NewReader(input))
	lineNum := 0

	for scanner.Scan() {
		lineNum++
		line := strings.TrimSpace(scanner.Text())

		// Пропускаем пустые строки и комментарии
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		// Секция [name] или [name.sub]
		if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
			currentSection = line[1 : len(line)-1]
			if _, ok := doc[currentSection]; !ok {
				doc[currentSection] = make(map[string]Value)
			}
			continue
		}

		// key = value
		eqIdx := strings.Index(line, "=")
		if eqIdx < 0 {
			return nil, fmt.Errorf("line %d: expected '='", lineNum)
		}

		key := strings.TrimSpace(line[:eqIdx])
		raw := strings.TrimSpace(line[eqIdx+1:])

		val, err := parseValue(raw)
		if err != nil {
			return nil, fmt.Errorf("line %d: %w", lineNum, err)
		}

		if currentSection == "" {
			currentSection = "_root"
			doc[currentSection] = make(map[string]Value)
		}
		doc[currentSection][key] = val
	}

	return doc, scanner.Err()
}

func parseValue(raw string) (Value, error) {
	// Массив ["a", "b"]
	if strings.HasPrefix(raw, "[") {
		inner := strings.TrimPrefix(strings.TrimSuffix(raw, "]"), "[")
		var arr []string
		for _, item := range strings.Split(inner, ",") {
			item = strings.TrimSpace(item)
			item = strings.Trim(item, `"'`)
			if item != "" {
				arr = append(arr, item)
			}
		}
		return Value{Array: arr, IsArr: true}, nil
	}

	// Строка "value" или 'value'
	if (strings.HasPrefix(raw, `"`) && strings.HasSuffix(raw, `"`)) ||
		(strings.HasPrefix(raw, `'`) && strings.HasSuffix(raw, `'`)) {
		return Value{Str: raw[1 : len(raw)-1]}, nil
	}

	// Число или bool без кавычек
	return Value{Str: raw}, nil
}

// GetStr возвращает строковое значение по секции и ключу
func (d Document) GetStr(section, key string) string {
	if s, ok := d[section]; ok {
		if v, ok := s[key]; ok {
			return v.Str
		}
	}
	return ""
}

// GetArr возвращает массив строк
func (d Document) GetArr(section, key string) []string {
	if s, ok := d[section]; ok {
		if v, ok := s[key]; ok && v.IsArr {
			return v.Array
		}
	}
	return nil
}

// Sections возвращает все секции с заданным префиксом
func (d Document) Sections(prefix string) []string {
	var result []string
	for k := range d {
		if strings.HasPrefix(k, prefix) {
			result = append(result, k)
		}
	}
	return result
}
