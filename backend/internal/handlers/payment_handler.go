package handlers

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"errors"

	"github.com/gin-gonic/gin"
	"github.com/go-playground/validator/v10"
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
		Period      int     `json:"period", binding: "gte=0"`
		DeviceType  string  `json:"device_type" binding:"required"`
		PaymentType string  `json:"payment_type" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		// Логируем ошибки валидации
		var validationErrors validator.ValidationErrors
		if errors.As(err, &validationErrors) {
			for _, e := range validationErrors {
				h.logger.Error("Validation error", map[string]interface{}{
					"field":   e.Field(),
					"tag":     e.Tag(),
					"value":   e.Value(),
					"message": e.Error(),
				})
			}
		} else {
			h.logger.Error("Failed to parse JSON", map[string]interface{}{
				"error": err.Error(),
			})
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body", "details": err.Error()})
		return
	}

	// Логируем успешный парсинг
	h.logger.Info("Parsed request", map[string]interface{}{
		"user_id":      request.UserID,
		"amount":       request.Amount,
		"period":       request.Period,
		"device_type":  request.DeviceType,
		"payment_type": request.PaymentType,
	})

	// Validate payment type
	if request.PaymentType != "ukassa" && request.PaymentType != "crypto" {
		h.logger.Error("Invalid payment type", map[string]interface{}{"payment_type": request.PaymentType})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid payment type"})
		return
	}

	// Initiate deposit
	paymentID, err := h.paymentService.InitiateDeposit(request.UserID, request.Amount, request.Period, request.DeviceType, request.PaymentType)
	if err != nil {
		h.logger.Error("Failed to initiate deposit", map[string]interface{}{
			"error":        err.Error(),
			"user_id":      request.UserID,
			"amount":       request.Amount,
			"period":       request.Period,
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
	// Read raw body for signature verification
	bodyBytes, err := io.ReadAll(c.Request.Body)
	if err != nil {
		h.logger.Error("Failed to read request body", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
		return
	}
	c.Request.Body = io.NopCloser(strings.NewReader(string(bodyBytes)))

	// Verify Ukassa signature
	signature := c.GetHeader("X-Yoo-Signature") // Adjust based on Ukassa docs
	if !verifyUkassaSignature(bodyBytes, signature) {
		h.logger.Error("Invalid Ukassa signature")
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid signature"})
		return
	}

	// Parse request body
	var request struct {
		Event  string `json:"event" binding:"required"`
		Object struct {
			ID     string `json:"id" binding:"required"`
			Status string `json:"status" binding:"required"`
			Amount struct {
				Value    string `json:"value" binding:"required"`
				Currency string `json:"currency"`
			} `json:"amount" binding:"required"`
			Metadata struct {
				UserID      string `json:"user_id" binding:"required"`
				Period      string `json:"period" binding:"required"`
				DeviceType  string `json:"device_type" binding:"required"`
				PaymentType string `json:"payment_type" binding:"required"`
			} `json:"metadata" binding:"required"`
		} `json:"object" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid webhook payload", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid webhook payload"})
		return
	}

	// Validate and convert fields
	userID, err := strconv.Atoi(request.Object.Metadata.UserID)
	if err != nil {
		h.logger.Error("Invalid user_id", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id"})
		return
	}

	amount, err := strconv.ParseFloat(request.Object.Amount.Value, 64)
	if err != nil {
		h.logger.Error("Invalid amount", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid amount"})
		return
	}

	period, err := strconv.Atoi(request.Object.Metadata.Period)
	if err != nil {
		h.logger.Error("Invalid period", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid period"})
		return
	}

	// Process payment
	err = h.paymentService.ProcessWebhookPayment(
		userID,
		amount,
		period,
		request.Object.Metadata.DeviceType,
		request.Object.Metadata.PaymentType,
		request.Object.ID,
		request.Object.Status,
	)
	if err != nil {
		h.logger.Error("Failed to process payment", map[string]interface{}{
			"error":        err.Error(),
			"payment_id":   request.Object.ID,
			"status":       request.Object.Status,
			"user_id":      userID,
			"amount":       amount,
			"period":       period,
			"device_type":  request.Object.Metadata.DeviceType,
			"payment_type": request.Object.Metadata.PaymentType,
		})
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to process payment"})
		return
	}

	h.logger.Info("Ukassa payment processed", map[string]interface{}{
		"payment_id":   request.Object.ID,
		"status":       request.Object.Status,
		"user_id":      userID,
		"amount":       amount,
		"period":       period,
		"device_type":  request.Object.Metadata.DeviceType,
		"payment_type": request.Object.Metadata.PaymentType,
	})

	c.JSON(http.StatusOK, gin.H{"status": "Processed"})
}

// ProcessCryptoWebhook handles POST /payments/crypto
func (h *PaymentHandler) ProcessCryptoWebhook(c *gin.Context) {
	// Read raw body for signature verification
	bodyBytes, err := io.ReadAll(c.Request.Body)
	if err != nil {
		h.logger.Error("Failed to read request body", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
		return
	}
	c.Request.Body = io.NopCloser(strings.NewReader(string(bodyBytes)))

	// Verify CryptoBot signature
	signature := c.GetHeader("crypto-pay-api-signature")
	if !verifyCryptoSignature(bodyBytes, signature) {
		h.logger.Error("Invalid CryptoBot signature")
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid signature"})
		return
	}

	// Parse request body
	var request struct {
		UpdateID   int64  `json:"update_id" binding:"required"`
		UpdateType string `json:"update_type" binding:"required"`
		InvoiceID  string `json:"invoice_id" binding:"required"`
		Amount     string `json:"amount" binding:"required"`
		Currency   string `json:"currency"`
		Payload    string `json:"payload" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid webhook payload", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid webhook payload"})
		return
	}

	// Parse payload (e.g., "user_id:123,period:3,payment_type:device_subscription")
	payloadFields, err := parseCryptoPayload(request.Payload)
	if err != nil {
		h.logger.Error("Invalid payload", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid payload"})
		return
	}

	userID, err := strconv.Atoi(payloadFields["user_id"])
	if err != nil {
		h.logger.Error("Invalid user_id", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id"})
		return
	}

	period, err := strconv.Atoi(payloadFields["period"])
	if err != nil {
		h.logger.Error("Invalid period", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid period"})
		return
	}

	paymentType := payloadFields["payment_type"]
	if paymentType == "" {
		h.logger.Error("Missing payment_type")
		c.JSON(http.StatusBadRequest, gin.H{"error": "Missing payment_type"})
		return
	}

	deviceType := payloadFields["device_type"]
	if paymentType == "" {
		h.logger.Error("Missing device_type")
		c.JSON(http.StatusBadRequest, gin.H{"error": "Missing device_type"})
		return
	}

	amount, err := strconv.ParseFloat(request.Amount, 64)
	if err != nil {
		h.logger.Error("Invalid amount", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid amount"})
		return
	}

	// Process payment
	err = h.paymentService.ProcessWebhookPayment(
		userID,
		amount,
		period,
		deviceType,
		paymentType,
		request.InvoiceID,
		request.UpdateType,
	)
	if err != nil {
		h.logger.Error("Failed to process payment", map[string]interface{}{
			"error":        err.Error(),
			"payment_id":   request.InvoiceID,
			"status":       request.UpdateType,
			"user_id":      userID,
			"amount":       amount,
			"period":       period,
			"device_type":  deviceType,
			"payment_type": paymentType,
		})
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to process payment"})
		return
	}

	h.logger.Info("Crypto payment processed", map[string]interface{}{
		"payment_id":   request.InvoiceID,
		"status":       request.UpdateType,
		"user_id":      userID,
		"amount":       amount,
		"period":       period,
		"device_type":  deviceType,
		"payment_type": paymentType,
	})

	c.JSON(http.StatusOK, gin.H{"status": "Processed"})
}

// verifyUkassaSignature verifies the Ukassa webhook signature
func verifyUkassaSignature(body []byte, signature string) bool {
	secret := []byte(os.Getenv("UKASSA_WEBHOOK_SECRET"))
	hash := hmac.New(sha256.New, secret)
	hash.Write(body)
	expected := hex.EncodeToString(hash.Sum(nil))
	return signature == expected
}

// verifyCryptoSignature verifies the CryptoBot webhook signature
func verifyCryptoSignature(body []byte, signature string) bool {
	if signature == "" {
		log.Println("Missing crypto-pay-api-signature header")
		return false
	}
	secret := []byte(os.Getenv("CRYPTOBOT_API_TOKEN"))
	hash := hmac.New(sha256.New, secret)
	hash.Write(body)
	expected := hex.EncodeToString(hash.Sum(nil))
	return signature == expected
}

// parseCryptoPayload parses CryptoBot payload (e.g., "user_id:123,period:3,payment_type:device_subscription")
func parseCryptoPayload(payload string) (map[string]string, error) {
	fields := map[string]string{}
	pairs := strings.Split(payload, ",")
	for _, pair := range pairs {
		parts := strings.Split(pair, ":")
		if len(parts) != 2 || parts[0] == "" || parts[1] == "" {
			return nil, fmt.Errorf("invalid payload format: %s", pair)
		}
		fields[parts[0]] = parts[1]
	}
	requiredFields := []string{"user_id", "period", "device_type", "payment_type"}
	for _, field := range requiredFields {
		if fields[field] == "" {
			return nil, fmt.Errorf("missing required field: %s", field)
		}
	}
	return fields, nil
}

// ProcessBalancePayment handles POST /payments/balance
func (h *PaymentHandler) ProcessBalancePayment(c *gin.Context) {
	// Parse request body
	var request struct {
		UserID      int     `json:"user_id" binding:"required"`
		Amount      float64 `json:"amount" binding:"required,gt=0"`
		Period      int     `json:"period" binding: "gte=0"`
		DeviceType  string  `json:"device_type" binding:"required"`
		PaymentType string  `json:"payment_type" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		var validationErrors validator.ValidationErrors
		if errors.As(err, &validationErrors) {
			for _, e := range validationErrors {
				h.logger.Error("Validation error", map[string]interface{}{
					"field":   e.Field(),
					"tag":     e.Tag(),
					"value":   e.Value(),
					"message": e.Error(),
				})
			}
		} else {
			h.logger.Error("Failed to parse JSON", map[string]interface{}{
				"error": err.Error(),
			})
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body", "details": err.Error()})
		return
	}

	h.logger.Info("Parsed request in Handler", map[string]interface{}{
		"user_id":      request.UserID,
		"amount":       request.Amount,
		"period":       request.Period,
		"device_type":  request.DeviceType,
		"payment_type": request.PaymentType,
	})

	// Process balance payment
	err := h.paymentService.ProcessBalancePayment(request.UserID, request.Amount, request.Period, request.DeviceType, request.PaymentType)
	if err != nil {
		h.logger.Error("Failed to process balance payment", map[string]interface{}{
			"error":        err.Error(),
			"user_id":      request.UserID,
			"amount":       request.Amount,
			"period":       request.Period,
			"device_type":  request.DeviceType,
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
		"period":       request.Period,
		"device_type":  request.DeviceType,
		"payment_type": request.PaymentType,
	})

	c.JSON(http.StatusOK, gin.H{"status": "Payment successful"})
}
