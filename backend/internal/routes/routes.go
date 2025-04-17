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

		// Subscription routes
		api.GET("/subscriptions/:user_id/:type", h.SubscriptionHandler.GetSubscription)
		api.POST("/subscriptions", h.SubscriptionHandler.CreateSubscription)
		api.PUT("/subscriptions/:id/duration", h.SubscriptionHandler.UpdateDuration)
	}

	// Webhook routes (may have different authentication)
	r.POST("/payments/ukassa", h.PaymentHandler.ProcessUkassaWebhook)
	r.POST("/payments/crypto", h.PaymentHandler.ProcessCryptoWebhook)
}
