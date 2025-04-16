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
