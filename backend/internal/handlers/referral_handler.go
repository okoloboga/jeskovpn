package handlers

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/okoloboga/backend/internal/services"
	"github.com/okoloboga/backend/pkg/logger"
)

// ReferralHandler handles referral-related requests
type ReferralHandler struct {
	referralService services.ReferralService
	logger          logger.Logger
}

// NewReferralHandler creates a new referral handler
func NewReferralHandler(referralService services.ReferralService, logger logger.Logger) *ReferralHandler {
	return &ReferralHandler{
		referralService: referralService,
		logger:          logger,
	}
}

// AddReferral handles POST /referrals
func (h *ReferralHandler) AddReferral(c *gin.Context) {
	// Parse request body
	var request struct {
		Payload string `json:"payload" binding:"required"` // referrer_id
		UserID  string `json:"user_id" binding:"required"` // user_id
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid request body", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	// Convert string IDs to integers
	userID, err := strconv.Atoi(request.UserID)
	if err != nil {
		h.logger.Error("Invalid user_id format", map[string]interface{}{"user_id": request.UserID})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id"})
		return
	}

	referrerID, err := strconv.Atoi(request.Payload)
	if err != nil {
		h.logger.Error("Invalid referrer_id format", map[string]interface{}{"referrer_id": request.Payload})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid referrer_id"})
		return
	}

	// Add referral
	err = h.referralService.AddReferral(userID, referrerID)
	if err != nil {
		h.logger.Error("Failed to add referral", map[string]interface{}{
			"error":       err.Error(),
			"user_id":     userID,
			"referrer_id": referrerID,
		})

		// Check for specific errors
		if err.Error() == "user not found" || err.Error() == "referrer not found" {
			c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to add referral"})
		return
	}

	h.logger.Info("Referral added", map[string]interface{}{
		"user_id":     userID,
		"referrer_id": referrerID,
	})

	c.JSON(http.StatusOK, gin.H{"status": "Referral added"})
}
