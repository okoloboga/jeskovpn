package main

import (
	"fmt"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/okoloboga/jeskovpn/backend/internal/config"
	"github.com/okoloboga/jeskovpn/backend/internal/handlers"
	"github.com/okoloboga/jeskovpn/backend/internal/middleware"
	"github.com/okoloboga/jeskovpn/backend/internal/repositories"
	"github.com/okoloboga/jeskovpn/backend/internal/routes"
	"github.com/okoloboga/jeskovpn/backend/internal/services"
	"github.com/okoloboga/jeskovpn/backend/pkg/logger"
	"github.com/okoloboga/jeskovpn/backend/pkg/vpn"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func main() {
	// Initialize logger
	appLogger := logger.New("info")
	appLogger.Info("Starting VPN Backend API")

	// Load configuration
	cfg, err := config.LoadConfig()
	if err != nil {
		// handle error, e.g. log.Fatal(err)
	}

	// Connect to database
	dsn := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		cfg.DB.Host, cfg.DB.Port, cfg.DB.User,
		cfg.DB.Password, cfg.DB.Name)

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		appLogger.Error("Failed to connect to database", map[string]interface{}{"error": err.Error()})
		panic("Failed to connect to database")
	}

	// Initialize repositories
	userRepo := repositories.NewUserRepository(db)
	deviceRepo := repositories.NewDeviceRepository(db)
	referralRepo := repositories.NewReferralRepository(db)
	ticketRepo := repositories.NewTicketRepository(db)
	transactionRepo := repositories.NewTransactionRepository(db)

	// Initialize VPN key generator
	vpnGenerator := vpn.NewOutlineGenerator(cfg.Outline.APIUrl, cfg.Outline.APIKey)

	// Initialize services
	userService := services.NewUserService(userRepo, deviceRepo)
	deviceService := services.NewDeviceService(deviceRepo, userRepo, vpnGenerator)
	referralService := services.NewReferralService(referralRepo, userRepo)
	ticketService := services.NewTicketService(ticketRepo)
	paymentService := services.NewPaymentService(transactionRepo, userRepo)

	// Initialize handlers
	h := &handlers.Handlers{
		UserHandler:     handlers.NewUserHandler(userService, appLogger),
		ReferralHandler: handlers.NewReferralHandler(referralService, appLogger),
		TicketHandler:   handlers.NewTicketHandler(ticketService, appLogger),
		PaymentHandler:  handlers.NewPaymentHandler(paymentService, appLogger),
		DeviceHandler:   handlers.NewDeviceHandler(deviceService, appLogger),
	}

	// Initialize middleware
	authMiddleware := middleware.AuthMiddleware(cfg.APIToken)

	// Setup router
	r := gin.Default()

	// Register routes
	routes.SetupRoutes(r, h, authMiddleware)

	// Start server
	appLogger.Info("Server starting on port " + strconv.Itoa(cfg.Port))
	if err := r.Run(":" + strconv.Itoa(cfg.Port)); err != nil {
		appLogger.Error("Failed to start server", map[string]interface{}{"error": err.Error()})
		panic("Failed to start server")
	}
}
