package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/okoloboga/jeskovpn/backend/internal/services"
	"github.com/okoloboga/jeskovpn/backend/pkg/logger"
)

// PaymentHandler handles payment-related requests
type PaymentHandler struct {
	paymentService services.PaymentService
	logger         logger.Logger
}

// NewPaymentHandler creates a new payment handler
func NewPaymentHandler(paymentService services.PaymentService, logger logger.Logger) *PaymentHandler {
	return &PaymentHandler{
		paymentService: paymentService,
		logger:         logger,
	}
}

// Deposit handles POST /payments/deposit
func (h *PaymentHandler) Deposit(c *gin.Context) {
	// Parse request body
	var request struct {
		UserID      int     `json:"user_id" binding:"required"`
		Amount      float64 `json:"amount" binding:"required,gt=0"`
		PaymentType string  `json:"payment_type" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid request body", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	// Validate payment type
	if request.PaymentType != "ukassa" && request.PaymentType != "crypto" && request.PaymentType != "stars" {
		h.logger.Error("Invalid payment type", map[string]interface{}{"payment_type": request.PaymentType})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid payment type"})
		return
	}

	// Initiate deposit
	paymentID, err := h.paymentService.InitiateDeposit(request.UserID, request.Amount, request.PaymentType)
	if err != nil {
		h.logger.Error("Failed to initiate deposit", map[string]interface{}{
			"error":        err.Error(),
			"user_id":      request.UserID,
			"amount":       request.Amount,
			"payment_type": request.PaymentType,
		})

		if err.Error() == "user not found" {
			c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
			return
		}

		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to initiate deposit"})
		return
	}

	h.logger.Info("Deposit initiated", map[string]interface{}{
		"user_id":      request.UserID,
		"amount":       request.Amount,
		"payment_type": request.PaymentType,
		"payment_id":   paymentID,
	})

	// For a real implementation, you would return a payment URL or other payment details
	// This is a simplified response
	c.JSON(http.StatusOK, gin.H{
		"status":      "Deposit initiated",
		"payment_id":  paymentID,
		"payment_url": "https://payment-provider.com/pay/" + paymentID,
	})
}

// ProcessUkassaWebhook handles POST /payments/ukassa
func (h *PaymentHandler) ProcessUkassaWebhook(c *gin.Context) {
	// Parse request body
	var request struct {
		UserID    int     `json:"user_id" binding:"required"`
		Amount    float64 `json:"amount" binding:"required"`
		PaymentID string  `json:"payment_id" binding:"required"`
		Status    string  `json:"status" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid webhook payload", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid webhook payload"})
		return
	}

	// Process payment
	err := h.paymentService.ProcessPayment(request.PaymentID, request.Status)
	if err != nil {
		h.logger.Error("Failed to process payment", map[string]interface{}{
			"error":      err.Error(),
			"payment_id": request.PaymentID,
			"status":     request.Status,
		})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Failed to process payment"})
		return
	}

	h.logger.Info("Payment processed", map[string]interface{}{
		"payment_id": request.PaymentID,
		"status":     request.Status,
		"user_id":    request.UserID,
		"amount":     request.Amount,
	})

	c.JSON(http.StatusOK, gin.H{"status": "Processed"})
}

// ProcessCryptoWebhook handles POST /payments/crypto
func (h *PaymentHandler) ProcessCryptoWebhook(c *gin.Context) {
	// Parse request body
	var request struct {
		UserID    int     `json:"user_id" binding:"required"`
		Amount    float64 `json:"amount" binding:"required"`
		PaymentID string  `json:"payment_id" binding:"required"`
		Status    string  `json:"status" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid webhook payload", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid webhook payload"})
		return
	}

	// Process payment
	err := h.paymentService.ProcessPayment(request.PaymentID, request.Status)
	if err != nil {
		h.logger.Error("Failed to process payment", map[string]interface{}{
			"error":      err.Error(),
			"payment_id": request.PaymentID,
			"status":     request.Status,
		})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Failed to process payment"})
		return
	}

	h.logger.Info("Crypto payment processed", map[string]interface{}{
		"payment_id": request.PaymentID,
		"status":     request.Status,
		"user_id":    request.UserID,
		"amount":     request.Amount,
	})

	c.JSON(http.StatusOK, gin.H{"status": "Processed"})
}

// ProcessBalancePayment handles POST /payments/balance
func (h *PaymentHandler) ProcessBalancePayment(c *gin.Context) {
	// Parse request body
	var request struct {
		UserID      int     `json:"user_id" binding:"required"`
		Amount      float64 `json:"amount" binding:"required,gt=0"`
		PaymentType string  `json:"payment_type" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid request body", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	// Process balance payment
	err := h.paymentService.ProcessBalancePayment(request.UserID, request.Amount, request.PaymentType)
	if err != nil {
		h.logger.Error("Failed to process balance payment", map[string]interface{}{
			"error":        err.Error(),
			"user_id":      request.UserID,
			"amount":       request.Amount,
			"payment_type": request.PaymentType,
		})

		if err.Error() == "user not found" {
			c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
			return
		}

		if err.Error() == "insufficient balance" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Insufficient balance"})
			return
		}

		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to process payment"})
		return
	}

	h.logger.Info("Balance payment processed", map[string]interface{}{
		"user_id":      request.UserID,
		"amount":       request.Amount,
		"payment_type": request.PaymentType,
	})

	c.JSON(http.StatusOK, gin.H{"status": "Payment successful"})
}
