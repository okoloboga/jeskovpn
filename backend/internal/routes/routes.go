// internal/routes/routes.go
package routes

import (
	"github.com/gin-gonic/gin"
	"github.com/okoloboga/jeskovpn/backend/internal/handlers"
)

// SetupRoutes configures all API routes
func SetupRoutes(r *gin.Engine, h *handlers.Handlers, authMiddleware gin.HandlerFunc) {
	// Public routes (no authentication required)
	r.POST("/users", h.UserHandler.CreateUser)

	// Protected routes (require authentication)
	api := r.Group("")
	api.Use(authMiddleware)
	{
		// User routes
		api.GET("/users/:user_id", h.UserHandler.GetUser)
		api.POST("/users/create", h.UserHandler.CreateUser)

		// Referral routes
		api.POST("/referrals", h.ReferralHandler.AddReferral)

		// Ticket routes
		api.POST("/tickets", h.TicketHandler.CreateTicket)
		api.GET("/tickets/:user_id", h.TicketHandler.GetTicket)
		api.DELETE("/tickets/:user_id", h.TicketHandler.DeleteTicket)

		// Payment routes
		api.POST("/payments/deposit", h.PaymentHandler.Deposit)
		api.POST("/payments/balance", h.PaymentHandler.ProcessBalancePayment)

		// Device routes
		api.POST("/devices/key", h.DeviceHandler.GenerateKey)
		api.DELETE("/devices/key", h.DeviceHandler.RevokeKey)
	}

	// Unauthenticated routes (for webhooks)
	apiNoAuth := r.Group("/api")
	{
		apiNoAuth.POST("/payments/ukassa", h.PaymentHandler.ProcessUkassaWebhook)
		apiNoAuth.POST("/payments/crypto", h.PaymentHandler.ProcessCryptoWebhook)
	}
}
