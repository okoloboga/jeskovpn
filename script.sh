#!/bin/bash

# Название проекта
PROJECT_NAME="vpn-bot-backend"

# Создаем корневую директорию проекта
mkdir -p $PROJECT_NAME
cd $PROJECT_NAME

# Создаем основные директории
mkdir -p cmd/api
mkdir -p internal/{config,models,repositories,services,handlers,middleware,utils}
mkdir -p migrations
mkdir -p pkg/{logger,vpn,payment}
mkdir -p docs

# Создаем файлы в cmd/api
cat > cmd/api/main.go << 'EOF'
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
EOF

# Создаем файлы конфигурации
cat > internal/config/config.go << 'EOF'
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
EOF

# Создаем модели
cat > internal/models/user.go << 'EOF'
package models

import (
	"time"
)

// User представляет пользователя в системе
type User struct {
	UserID    int       `gorm:"primaryKey" json:"user_id"`
	FirstName string    `json:"first_name"`
	LastName  string    `json:"last_name"`
	Username  string    `json:"username"`
	Balance   float64   `json:"balance"`
	CreatedAt time.Time `json:"created_at"`
}

// UserResponse представляет ответ с данными пользователя
type UserResponse struct {
	UserID       int                    `json:"user_id"`
	Balance      float64                `json:"balance"`
	Subscription SubscriptionCollection `json:"subscription"`
}

// SubscriptionCollection представляет коллекцию подписок пользователя
type SubscriptionCollection struct {
	Device DeviceSubscription `json:"device"`
	Router RouterSubscription `json:"router"`
	Combo  ComboSubscription  `json:"combo"`
}

// DeviceSubscription представляет подписку для устройств
type DeviceSubscription struct {
	Devices  []string `json:"devices"`
	Duration int      `json:"duration"`
}

// RouterSubscription представляет подписку для роутеров
type RouterSubscription struct {
	Duration int `json:"duration"`
}

// ComboSubscription представляет комбинированную подписку
type ComboSubscription struct {
	Devices  []string `json:"devices"`
	Duration int      `json:"duration"`
	Type     int      `json:"type"`
}
EOF

cat > internal/models/subscription.go << 'EOF'
package models

import (
	"time"
)

// Subscription представляет подписку пользователя
type Subscription struct {
	ID        int       `gorm:"primaryKey" json:"id"`
	UserID    int       `json:"user_id"`
	Type      string    `json:"type"` // device, router, combo
	Duration  int       `json:"duration"`
	ComboType int       `json:"combo_type"`
	ExpiresAt time.Time `json:"expires_at"`
}
EOF

cat > internal/models/device.go << 'EOF'
package models

import (
	"time"
)

// Device представляет устройство пользователя
type Device struct {
	ID             int       `gorm:"primaryKey" json:"id"`
	UserID         int       `json:"user_id"`
	SubscriptionID int       `json:"subscription_id"`
	DeviceName     string    `json:"device_name"`
	VpnKey         string    `json:"vpn_key"`
	CreatedAt      time.Time `json:"created_at"`
}
EOF

cat > internal/models/referral.go << 'EOF'
package models

import (
	"time"
)

// Referral представляет реферальную связь между пользователями
type Referral struct {
	ID         int       `gorm:"primaryKey" json:"id"`
	UserID     int       `json:"user_id"`      // Приглашенный пользователь
	ReferrerID int       `json:"referrer_id"`  // Пригласивший пользователь
	CreatedAt  time.Time `json:"created_at"`
}
EOF

cat > internal/models/ticket.go << 'EOF'
package models

import (
	"time"
)

// Ticket представляет тикет поддержки
type Ticket struct {
	ID        int       `gorm:"primaryKey" json:"id"`
	UserID    int       `json:"user_id"`
	Username  string    `json:"username"`
	Content   string    `json:"content"`
	CreatedAt time.Time `json:"created_at"`
}
EOF

cat > internal/models/transaction.go << 'EOF'
package models

import (
	"time"
)

// Transaction представляет финансовую транзакцию
type Transaction struct {
	ID          int       `gorm:"primaryKey" json:"id"`
	UserID      int       `json:"user_id"`
	Amount      float64   `json:"amount"`
	PaymentType string    `json:"payment_type"` // ukassa, crypto, balance, stars
	Status      string    `json:"status"`       // pending, succeeded, failed
	PaymentID   string    `json:"payment_id"`
	CreatedAt   time.Time `json:"created_at"`
}
EOF

# Создаем файлы репозиториев
cat > internal/repositories/user_repository.go << 'EOF'
package repositories

import (
	"vpn-bot-backend/internal/models"
	"gorm.io/gorm"
)

// UserRepository представляет репозиторий для работы с пользователями
type UserRepository struct {
	db *gorm.DB
}

// NewUserRepository создает новый репозиторий пользователей
func NewUserRepository(db *gorm.DB) *UserRepository {
	return &UserRepository{db: db}
}

// GetByID получает пользователя по ID
func (r *UserRepository) GetByID(userID int) (*models.User, error) {
	var user models.User
	result := r.db.First(&user, userID)
	return &user, result.Error
}

// Create создает нового пользователя
func (r *UserRepository) Create(user *models.User) error {
	return r.db.Create(user).Error
}

// Update обновляет данные пользователя
func (r *UserRepository) Update(user *models.User) error {
	return r.db.Save(user).Error
}

// Exists проверяет существование пользователя
func (r *UserRepository) Exists(userID int) (bool, error) {
	var count int64
	err := r.db.Model(&models.User{}).Where("user_id = ?", userID).Count(&count).Error
	return count > 0, err
}
EOF

# Создаем файлы сервисов
cat > internal/services/user_service.go << 'EOF'
package services

import (
	"errors"
	"time"
	
	"vpn-bot-backend/internal/models"
	"vpn-bot-backend/internal/repositories"
)

// UserService представляет сервис для работы с пользователями
type UserService struct {
	userRepo        *repositories.UserRepository
	subscriptionRepo *repositories.SubscriptionRepository
	deviceRepo      *repositories.DeviceRepository
}

// NewUserService создает новый сервис пользователей
func NewUserService(
	userRepo *repositories.UserRepository,
	subscriptionRepo *repositories.SubscriptionRepository,
	deviceRepo *repositories.DeviceRepository,
) *UserService {
	return &UserService{
		userRepo:        userRepo,
		subscriptionRepo: subscriptionRepo,
		deviceRepo:      deviceRepo,
	}
}

// GetUser получает данные пользователя с подписками
func (s *UserService) GetUser(userID int) (*models.UserResponse, error) {
	user, err := s.userRepo.GetByID(userID)
	if err != nil {
		return nil, err
	}
	
	// Здесь будет логика получения подписок и устройств
	// Это заглушка, которую нужно будет заменить реальной логикой
	
	return &models.UserResponse{
		UserID:  user.UserID,
		Balance: user.Balance,
		Subscription: models.SubscriptionCollection{
			Device: models.DeviceSubscription{
				Devices:  []string{"android", "iphone"},
				Duration: 3,
			},
			Router: models.RouterSubscription{
				Duration: 0,
			},
			Combo: models.ComboSubscription{
				Devices:  []string{},
				Duration: 0,
				Type:     0,
			},
		},
	}, nil
}

// CreateUser создает нового пользователя
func (s *UserService) CreateUser(userID int, firstName, lastName, username string) error {
	exists, err := s.userRepo.Exists(userID)
	if err != nil {
		return err
	}
	
	if exists {
		return errors.New("user already exists")
	}
	
	user := &models.User{
		UserID:    userID,
		FirstName: firstName,
		LastName:  lastName,
		Username:  username,
		Balance:   0.0,
		CreatedAt: time.Now(),
	}
	
	return s.userRepo.Create(user)
}
EOF

# Создаем файлы обработчиков
cat > internal/handlers/handler.go << 'EOF'
package handlers

import (
	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
	
	"vpn-bot-backend/internal/config"
	"vpn-bot-backend/internal/repositories"
	"vpn-bot-backend/internal/services"
	"vpn-bot-backend/pkg/logger"
)

// Handler содержит все обработчики API
type Handler struct {
	userService      *services.UserService
	referralService  *services.ReferralService
	ticketService    *services.TicketService
	paymentService   *services.PaymentService
	deviceService    *services.DeviceService
	logger           logger.Logger
}

// NewHandler создает новый экземпляр Handler
func NewHandler(db *gorm.DB, logger logger.Logger, cfg *config.Config) *Handler {
	// Инициализация репозиториев
	userRepo := repositories.NewUserRepository(db)
	subscriptionRepo := repositories.NewSubscriptionRepository(db)
	deviceRepo := repositories.NewDeviceRepository(db)
	referralRepo := repositories.NewReferralRepository(db)
	ticketRepo := repositories.NewTicketRepository(db)
	transactionRepo := repositories.NewTransactionRepository(db)
	
	// Инициализация сервисов
	userService := services.NewUserService(userRepo, subscriptionRepo, deviceRepo)
	referralService := services.NewReferralService(userRepo, referralRepo)
	ticketService := services.NewTicketService(ticketRepo)
	paymentService := services.NewPaymentService(userRepo, transactionRepo, cfg)
	deviceService := services.NewDeviceService(userRepo, subscriptionRepo, deviceRepo)
	
	return &Handler{
		userService:      userService,
		referralService:  referralService,
		ticketService:    ticketService,
		paymentService:   paymentService,
		deviceService:    deviceService,
		logger:           logger,
	}
}

// RegisterRoutes регистрирует все маршруты API
func (h *Handler) RegisterRoutes(router *gin.Engine) {
	api := router.Group("/api/v1")
	
	// Пользователи
	api.GET("/users/:user_id", h.GetUser)
	api.POST("/users", h.CreateUser)
	
	// Рефералы
	api.POST("/referrals", h.AddReferral)
	
	// Тикеты
	api.POST("/tickets", h.CreateTicket)
	api.GET("/tickets/:user_id", h.GetTicket)
	api.DELETE("/tickets/:user_id", h.DeleteTicket)
	
	// Платежи
	api.POST("/payments/deposit", h.Deposit)
	api.POST("/payments/ukassa", h.ProcessUkassaPayment)
	api.POST("/payments/crypto", h.ProcessCryptoPayment)
	api.POST("/payments/balance", h.ProcessBalancePayment)
	
	// Устройства
	api.POST("/devices/key", h.GenerateDeviceKey)
	api.DELETE("/devices/key", h.RemoveDeviceKey)
}
EOF

cat > internal/handlers/user_handler.go << 'EOF'
package handlers

import (
	"net/http"
	"strconv"
	
	"github.com/gin-gonic/gin"
)

// GetUser обрабатывает запрос на получение данных пользователя
func (h *Handler) GetUser(c *gin.Context) {
	userIDStr := c.Param("user_id")
	userID, err := strconv.Atoi(userIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id"})
		return
	}
	
	user, err := h.userService.GetUser(userID)
	if err != nil {
		h.logger.Error("Failed to get user", "error", err, "user_id", userID)
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}
	
	c.JSON(http.StatusOK, user)
}

// CreateUser обрабатывает запрос на создание нового пользователя
func (h *Handler) CreateUser(c *gin.Context) {
	var request struct {
		UserID    int    `json:"user_id" binding:"required"`
		FirstName string `json:"first_name" binding:"required"`
		LastName  string `json:"last_name"`
		Username  string `json:"username"`
	}
	
	if err := c.ShouldBindJSON(&request); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}
	
	err := h.userService.CreateUser(
		request.UserID,
		request.FirstName,
		request.LastName,
		request.Username,
	)
	
	if err != nil {
		h.logger.Error("Failed to create user", "error", err, "user_id", request.UserID)
		
		if err.Error() == "user already exists" {
			c.JSON(http.StatusConflict, gin.H{"error": "User already exists"})
			return
		}
		
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create user"})
		return
	}
	
	c.JSON(http.StatusCreated, gin.H{"status": "User created"})
}
EOF

# Создаем middleware
cat > internal/middleware/auth.go << 'EOF'
package middleware

import (
	"net/http"
	"strings"
	
	"github.com/gin-gonic/gin"
)

// Auth проверяет API-токен в заголовке Authorization
func Auth(apiToken string) gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		
		if authHeader == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Authorization header is required"})
			return
		}
		
		parts := strings.Split(authHeader, " ")
		if len(parts) != 2 || parts[0] != "Bearer" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Authorization header format must be Bearer {token}"})
			return
		}
		
		token := parts[1]
		if token != apiToken {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Invalid API token"})
			return
		}
		
		c.Next()
	}
}
EOF

cat > internal/middleware/logger.go << 'EOF'
package middleware

import (
	"time"
	
	"github.com/gin-gonic/gin"
	"vpn-bot-backend/pkg/logger"
)

// Logger логирует информацию о запросах
func Logger(log logger.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		
		// Обработка запроса
		c.Next()
		
		// Логирование после обработки
		latency := time.Since(start)
		statusCode := c.Writer.Status()
		clientIP := c.ClientIP()
		method := c.Request.Method
		
		log.Info("Request processed",
			"method", method,
			"path", path,
			"status", statusCode,
			"latency", latency,
			"ip", clientIP,
		)
	}
}
EOF

# Создаем пакет логгера
cat > pkg/logger/logger.go << 'EOF'
package logger

import (
	"os"
	
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

// Logger представляет интерфейс для логирования
type Logger interface {
	Debug(msg string, keysAndValues ...interface{})
	Info(msg string, keysAndValues ...interface{})
	Warn(msg string, keysAndValues ...interface{})
	Error(msg string, keysAndValues ...interface{})
	Fatal(msg string, keysAndValues ...interface{})
}

// zapLogger реализует интерфейс Logger с использованием zap
type zapLogger struct {
	logger *zap.SugaredLogger
}

// New создает новый экземпляр Logger
func New(level string) Logger {
	// Настройка уровня логирования
	var zapLevel zapcore.Level
	switch level {
	case "debug":
		zapLevel = zapcore.DebugLevel
	case "info":
		zapLevel = zapcore.InfoLevel
	case "warn":
		zapLevel = zapcore.WarnLevel
	case "error":
		zapLevel = zapcore.ErrorLevel
	default:
		zapLevel = zapcore.InfoLevel
	}
	
	// Настройка вывода
	encoderConfig := zap.NewProductionEncoderConfig()
	encoderConfig.TimeKey = "time"
	encoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
	
	core := zapcore.NewCore(
		zapcore.NewJSONEncoder(encoderConfig),
		zapcore.AddSync(os.Stdout),
		zapLevel,
	)
	
	logger := zap.New(core).Sugar()
	
	return &zapLogger{logger: logger}
}

func (l *zapLogger) Debug(msg string, keysAndValues ...interface{}) {
	l.logger.Debugw(msg, keysAndValues...)
}

func (l *zapLogger) Info(msg string, keysAndValues ...interface{}) {
	l.logger.Infow(msg, keysAndValues...)
}

func (l *zapLogger) Warn(msg string, keysAndValues ...interface{}) {
	l.logger.Warnw(msg, keysAndValues...)
}

func (l *zapLogger) Error(msg string, keysAndValues ...interface{}) {
	l.logger.Errorw(msg, keysAndValues...)
}

func (l *zapLogger) Fatal(msg string, keysAndValues ...interface{}) {
	l.logger.Fatalw(msg, keysAndValues...)
}
EOF

# Создаем пакет для генерации VPN-ключей
cat > pkg/vpn/generator.go << 'EOF'
package vpn

// KeyGenerator представляет интерфейс для генерации VPN-ключей
type KeyGenerator interface {
	GenerateKey(userID int, device string) (string, error)
	RevokeKey(userID int, device string) error
}
EOF

cat > pkg/vpn/wireguard.go << 'EOF'
package vpn

import (
	"fmt"
)

// WireGuardGenerator реализует генерацию ключей WireGuard
type WireGuardGenerator struct {
	// Здесь будут настройки для WireGuard
}

// NewWireGuardGenerator создает новый генератор ключей WireGuard
func NewWireGuardGenerator() *WireGuardGenerator {
	return &WireGuardGenerator{}
}

// GenerateKey генерирует новый ключ WireGuard
func (g *WireGuardGenerator) GenerateKey(userID int, device string) (string, error) {
	// Заглушка, которую нужно заменить реальной логикой
	// В реальной реализации здесь будет вызов wg-quick или другой утилиты
	return fmt.Sprintf("vpn_key_%d_%s", userID, device), nil
}

// RevokeKey отзывает ключ WireGuard
func (g *WireGuardGenerator) RevokeKey(userID int, device string) error {
	// Заглушка, которую нужно заменить реальной логикой
	return nil
}
EOF

# Создаем пакет для платежных систем
cat > pkg/payment/provider.go << 'EOF'
package payment

// PaymentProvider представляет интерфейс для платежных систем
type PaymentProvider interface {
	InitiatePayment(userID int, amount float64) (string, error)
	ProcessWebhook(payload []byte) (int, float64, string, error)
}
EOF

cat > pkg/payment/ukassa.go << 'EOF'
package payment

import (
	"encoding/json"
	"fmt"
)

// UkassaProvider реализует интеграцию с ЮKassa
type UkassaProvider struct {
	ShopID    string
	SecretKey string
	ReturnURL string
}

// NewUkassaProvider создает новый провайдер ЮKassa
func NewUkassaProvider(shopID, secretKey, returnURL string) *UkassaProvider {
	return &UkassaProvider{
		ShopID:    shopID,
		SecretKey: secretKey,
		ReturnURL: returnURL,
	}
}

// InitiatePayment инициирует платеж через ЮKassa
func (p *UkassaProvider) InitiatePayment(userID int, amount float64) (string, error) {
	// Заглушка, которую нужно заменить реальной логикой
	// В реальной реализации здесь будет вызов API ЮKassa
	return fmt.Sprintf("https://yookassa.ru/pay/%d", userID), nil
}

// ProcessWebhook обрабатывает webhook от ЮKassa
func (p *UkassaProvider) ProcessWebhook(payload []byte) (int, float64, string, error) {
	// Заглушка, которую нужно заменить реальной логикой
	var data struct {
		UserID    int     `json:"user_id"`
		Amount    float64 `json:"amount"`
		PaymentID string  `json:"payment_id"`
		Status    string  `json:"status"`
	}
	
	if err := json.Unmarshal(payload, &data); err != nil {
		return 0, 0, "", err
	}
	
	return data.UserID, data.Amount, data.Status, nil
}
EOF

# Создаем Dockerfile
cat > Dockerfile << 'EOF'
FROM golang:1.18-alpine AS builder

WORKDIR /app

# Копируем go.mod и go.sum
COPY go.mod go.sum ./
RUN go mod download

# Копируем исходный код
COPY . .

# Собираем приложение
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o vpnbot ./cmd/api

FROM alpine:3.15

WORKDIR /root/

# Устанавливаем зависимости
RUN apk --no-cache add ca-certificates

# Копируем бинарный файл из builder
COPY --from=builder /app/vpnbot .

# Открываем порт
EXPOSE 8080

# Запускаем приложение
CMD ["./vpnbot"]
EOF

# Создаем docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - APP_PORT=8080
      - LOG_LEVEL=info
      - API_TOKEN=your-api-token
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=postgres
      - DB_PASSWORD=postgres
      - DB_NAME=vpnbot
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:14-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=vpnbot
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

volumes:
  postgres-data:
EOF

# Создаем go.mod и go.sum
cat > go.mod << 'EOF'
module vpn-bot-backend

go 1.18

require (
	github.com/gin-gonic/gin v1.8.1
	go.uber.org/zap v1.21.0
	gorm.io/driver/postgres v1.3.8
	gorm.io/gorm v1.23.8
)

require (
	github.com/gin-contrib/sse v0.1.0 // indirect
	github.com/go-playground/locales v0.14.0 // indirect
	github.com/go-playground/universal-translator v0.18.0 // indirect
	github.com/go-playground/validator/v10 v10.11.0 // indirect
	github.com/goccy/go-json v0.9.10 // indirect
	github.com/jackc/chunkreader/v2 v2.0.1 // indirect
	github.com/jackc/pgconn v1.12.1 // indirect
	github.com/jackc/pgio v1.0.0 // indirect
	github.com/jackc/pgpassfile v1.0.0 // indirect
	github.com/jackc/pgproto3/v2 v2.3.0 // indirect
	github.com/jackc/pgservicefile v0.0.0-20200714003250-2b9c44734f2b // indirect
	github.com/jackc/pgtype v1.11.0 // indirect
	github.com/jackc/pgx/v4 v4.16.1 // indirect
	github.com/jinzhu/inflection v1.0.0 // indirect
	github.com/jinzhu/now v1.1.5 // indirect
	github.com/json-iterator/go v1.1.12 // indirect
	github.com/leodido/go-urn v1.2.1 // indirect
	github.com/mattn/go-isatty v0.0.14 // indirect
	github.com/modern-go/concurrent v0.0.0-20180306012644-bacd9c7ef1dd // indirect
	github.com/modern-go/reflect2 v1.0.2 // indirect
	github.com/pelletier/go-to
EOF
