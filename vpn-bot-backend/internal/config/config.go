package config

import (
	"os"
	"strconv"
)

// Config содержит все настройки приложения
type Config struct {
	Port     int
	LogLevel string
	APIToken string
	DB       DBConfig
}

// DBConfig содержит настройки базы данных
type DBConfig struct {
	Host     string
	Port     int
	User     string
	Password string
	Name     string
}

// Load загружает конфигурацию из переменных окружения
func Load() (*Config, error) {
	port, err := strconv.Atoi(getEnv("APP_PORT", "8080"))
	if err != nil {
		return nil, err
	}
	
	dbPort, err := strconv.Atoi(getEnv("DB_PORT", "5432"))
	if err != nil {
		return nil, err
	}
	
	return &Config{
		Port:     port,
		LogLevel: getEnv("LOG_LEVEL", "info"),
		APIToken: getEnv("API_TOKEN", "your-api-token"),
		DB: DBConfig{
			Host:     getEnv("DB_HOST", "localhost"),
			Port:     dbPort,
			User:     getEnv("DB_USER", "postgres"),
			Password: getEnv("DB_PASSWORD", "postgres"),
			Name:     getEnv("DB_NAME", "vpnbot"),
		},
	}, nil
}

// getEnv получает значение переменной окружения или возвращает значение по умолчанию
func getEnv(key, defaultValue string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultValue
}
