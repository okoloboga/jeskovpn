package main

import (
	"fmt"
	"log"
	"os"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/okoloboga/jeskovpn/backend/internal/config"
	"github.com/okoloboga/jeskovpn/backend/internal/handlers"
	"github.com/okoloboga/jeskovpn/backend/internal/middleware"
	"github.com/okoloboga/jeskovpn/backend/internal/models"
	"github.com/okoloboga/jeskovpn/backend/internal/repositories"
	"github.com/okoloboga/jeskovpn/backend/internal/routes"
	"github.com/okoloboga/jeskovpn/backend/internal/services"
	"github.com/okoloboga/jeskovpn/backend/pkg/logger"
	"github.com/okoloboga/jeskovpn/backend/pkg/vpn"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func ConnectDB() *gorm.DB {
	log.Println("Attempting to connect to database...")
	dsn := fmt.Sprintf("host=%s user=%s password=%s dbname=%s port=%s sslmode=disable",
		os.Getenv("DB_HOST"), os.Getenv("DB_USER"), os.Getenv("DB_PASSWORD"), os.Getenv("DB_NAME"), os.Getenv("DB_PORT"))
	log.Printf("DSN: %s", dsn)

	var db *gorm.DB
	var err error

	// Retry connection up to 5 times
	for i := 0; i < 5; i++ {
		db, err = gorm.Open(postgres.Open(dsn), &gorm.Config{})
		if err == nil {
			log.Println("Successfully connected to database")
			break
		}
		log.Printf("Failed to connect to database (attempt %d/5): %v", i+1, err)
		time.Sleep(5 * time.Second)
	}

	if err != nil {
		log.Fatal("Failed to connect to database after retries:", err)
	}

	// Test the connection
	sqlDB, err := db.DB()
	if err != nil {
		log.Fatal("Failed to get database instance:", err)
	}
	if err := sqlDB.Ping(); err != nil {
		log.Fatal("Failed to ping database:", err)
	}
	log.Println("Database ping successful")

	// Auto-migrate the User model (and other models if needed)
	log.Println("Running AutoMigrate for models")
	err = db.AutoMigrate(
		&models.User{},
		&models.Device{},
		&models.Payment{},
		&models.Referral{},
		&models.Ticket{},
	)
	if err != nil {
		log.Fatal("Failed to migrate database:", err)
	}
	log.Println("AutoMigrate completed successfully")

	return db
}

func main() {
	// Initialize logger
	appLogger := logger.New("info")
	appLogger.Info("Starting VPN Backend API")

	// Load configuration
	cfg, err := config.LoadConfig()
	if err != nil {
		appLogger.Error("Failed to load config", map[string]interface{}{"error": err.Error()})
		log.Fatal("Failed to load config:", err)
	}

	// Connect to database using ConnectDB
	db := ConnectDB()

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
		log.Fatal("Failed to start server:", err)
	}
}
