package handlers

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/okoloboga/jeskovpn/backend/internal/services"
	"github.com/okoloboga/jeskovpn/backend/pkg/logger"
)

// UserHandler handles user-related requests
type UserHandler struct {
	userService services.UserService
	logger      logger.Logger
}

// NewUserHandler creates a new user handler
func NewUserHandler(userService services.UserService, logger logger.Logger) *UserHandler {
	return &UserHandler{
		userService: userService,
		logger:      logger,
	}
}

// GetUser handles GET /users/:user_id
func (h *UserHandler) GetUser(c *gin.Context) {
	// Parse user_id from URL
	userID, err := strconv.Atoi(c.Param("user_id"))
	if err != nil {
		h.logger.Error("Invalid user_id format")
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id"})
		return
	}

	// Get user from service
	user, err := h.userService.GetUser(userID)
	if err != nil {
		h.logger.Error("Failed to get user", map[string]interface{}{"error": err.Error(), "user_id": userID})
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}

	// Format response according to API spec
	response := gin.H{
		"user_id": user.UserID,
		"balance": user.Balance,
		"subscription": gin.H{
			"device": gin.H{
				"devices":  []string{}, // This should be populated from the device service
				"duration": 0,          // This should be populated from the subscription service
			},
			"router": gin.H{
				"devices":  []string{},
				"duration": 0, // This should be populated from the subscription service
			},
			"combo": gin.H{
				"devices":  []string{}, // This should be populated from the device service
				"duration": 0,          // This should be populated from the subscription service
				"type":     0,          // This should be populated from the subscription service
			},
		},
	}

	c.JSON(http.StatusOK, response)
}

// CreateUser handles POST /users
func (h *UserHandler) CreateUser(c *gin.Context) {
	// Parse request body
	var request struct {
		UserID    int    `json:"user_id" binding:"required"`
		FirstName string `json:"first_name" binding:"required"`
		LastName  string `json:"last_name" binding:"required"`
		Username  string `json:"username" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid request body", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	// Create user
	err := h.userService.CreateUser(request.UserID, request.FirstName, request.LastName, request.Username)
	if err != nil {
		h.logger.Error("Failed to create user", map[string]interface{}{"error": err.Error(), "user_id": request.UserID})

		// Check for specific errors
		if err.Error() == "user already exists" {
			c.JSON(http.StatusConflict, gin.H{"error": "User already exists"})
			return
		}

		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create user"})
		return
	}

	h.logger.Info("User created", map[string]interface{}{"user_id": request.UserID, "username": request.Username})
	c.JSON(http.StatusCreated, gin.H{"status": "User created"})
}
