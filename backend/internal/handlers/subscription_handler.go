// internal/handlers/subscription_handler.go
package handlers

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/okoloboga/jeskovpn/backend/internal/services"
	"github.com/okoloboga/jeskovpn/backend/pkg/logger"
)

// SubscriptionHandler handles subscription-related requests
type SubscriptionHandler struct {
	subscriptionService services.SubscriptionService
	logger              logger.Logger
}

// NewSubscriptionHandler creates a new subscription handler
func NewSubscriptionHandler(subscriptionService services.SubscriptionService, logger logger.Logger) *SubscriptionHandler {
	return &SubscriptionHandler{
		subscriptionService: subscriptionService,
		logger:              logger,
	}
}

// GetSubscription handles GET /subscriptions/:user_id/:type
func (h *SubscriptionHandler) GetSubscription(c *gin.Context) {
	userID, err := strconv.Atoi(c.Param("user_id"))
	if err != nil {
		h.logger.Error("Invalid user_id format")
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id"})
		return
	}
	subType := c.Param("type")

	sub, err := h.subscriptionService.GetByUserID(userID, subType)
	if err != nil {
		h.logger.Error("Failed to get subscription", map[string]interface{}{"error": err.Error(), "user_id": userID, "type": subType})
		c.JSON(http.StatusNotFound, gin.H{"error": "Subscription not found"})
		return
	}

	c.JSON(http.StatusOK, sub)
}

// CreateSubscription handles POST /subscriptions
func (h *SubscriptionHandler) CreateSubscription(c *gin.Context) {
	var request struct {
		UserID    int    `json:"user_id" binding:"required"`
		Type      string `json:"type" binding:"required"`
		Duration  int    `json:"duration" binding:"required"`
		ComboType int    `json:"combo_type"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid request body", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	err := h.subscriptionService.Create(request.UserID, request.Type, request.Duration, request.ComboType)
	if err != nil {
		h.logger.Error("Failed to create subscription", map[string]interface{}{"error": err.Error(), "user_id": request.UserID})
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create subscription"})
		return
	}

	h.logger.Info("Subscription created", map[string]interface{}{"user_id": request.UserID, "type": request.Type})
	c.JSON(http.StatusCreated, gin.H{"status": "Subscription created"})
}

// UpdateDuration handles PUT /subscriptions/:id/duration
func (h *SubscriptionHandler) UpdateDuration(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		h.logger.Error("Invalid subscription id format")
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid subscription id"})
		return
	}

	var request struct {
		Duration int `json:"duration" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid request body", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	err = h.subscriptionService.UpdateDuration(id, request.Duration)
	if err != nil {
		h.logger.Error("Failed to update duration", map[string]interface{}{"error": err.Error(), "id": id})
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update duration"})
		return
	}

	h.logger.Info("Subscription duration updated", map[string]interface{}{"id": id, "duration": request.Duration})
	c.JSON(http.StatusOK, gin.H{"status": "Subscription duration updated"})
}
