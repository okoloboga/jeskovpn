package main

import (
	"fmt"
	"log"
	
	"github.com/gin-gonic/gin"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	
	"vpn-bot-backend/internal/config"
	"vpn-bot-backend/internal/handlers"
	"vpn-bot-backend/internal/middleware"
	"vpn-bot-backend/pkg/logger"
)

func main() {
	// Инициализация конфигурации
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}
	
	// Инициализация логгера
	l := logger.New(cfg.LogLevel)
	
	// Подключение к базе данных
	dsn := fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		cfg.DB.Host, cfg.DB.Port, cfg.DB.User, cfg.DB.Password, cfg.DB.Name,
	)
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		l.Fatal("Failed to connect to database", "error", err)
	}
	
	// Инициализация роутера
	router := gin.Default()
	
	// Добавление middleware
	router.Use(middleware.Logger(l))
	router.Use(middleware.Auth(cfg.APIToken))
	
	// Инициализация обработчиков
	h := handlers.NewHandler(db, l, cfg)
	
	// Регистрация маршрутов
	h.RegisterRoutes(router)
	
	// Запуск сервера
	l.Info("Starting server", "port", cfg.Port)
	if err := router.Run(fmt.Sprintf(":%d", cfg.Port)); err != nil {
		l.Fatal("Failed to start server", "error", err)
	}
}
