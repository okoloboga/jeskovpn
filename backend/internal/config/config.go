package config

import (
	"os"
	"strconv"
)

// Config contains all application settings
type Config struct {
	Port     int
	LogLevel string
	APIToken string
	Outline  OutlineGenerator
	DB       DBConfig
}

// DBConfig contains database settings
type DBConfig struct {
	Host     string
	Port     int
	User     string
	Password string
	Name     string
}

// OutlineGenerator contains Outline API settings
type OutlineGenerator struct {
	APIUrl string
	APIKey string
}

// Load loads configuration from environment variables
func LoadConfig() (*Config, error) {
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
		Outline: OutlineGenerator{
			APIUrl: getEnv("OUTLINE_API_URL", "https://api.outline.com"),
			APIKey: getEnv("OUTLINE_API_KEY", "your-outline-api-key"),
		},
		DB: DBConfig{
			Host:     getEnv("DB_HOST", "localhost"),
			Port:     dbPort,
			User:     getEnv("DB_USER", "postgres"),
			Password: getEnv("DB_PASSWORD", "postgres"),
			Name:     getEnv("DB_NAME", "vpnbot"),
		},
	}, nil
}

// getEnv returns the value of the environment variable if set, otherwise returns the default value
func getEnv(key, defaultValue string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultValue
}
