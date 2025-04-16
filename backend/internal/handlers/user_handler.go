package handlers

import (
	"net/http"
	"strconv"
	
	"github.com/gin-gonic/gin"
)

// GetUser обрабатывает запрос на получение данных пользователя
func (h *Handler) GetUser(c *gin.Context) {
	userIDStr := c.Param("user_id")
	userID, err := strconv.Atoi(userIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id"})
		return
	}
	
	user, err := h.userService.GetUser(userID)
	if err != nil {
		h.logger.Error("Failed to get user", "error", err, "user_id", userID)
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}
	
	c.JSON(http.StatusOK, user)
}

// CreateUser обрабатывает запрос на создание нового пользователя
func (h *Handler) CreateUser(c *gin.Context) {
	var request struct {
		UserID    int    `json:"user_id" binding:"required"`
		FirstName string `json:"first_name" binding:"required"`
		LastName  string `json:"last_name"`
		Username  string `json:"username"`
	}
	
	if err := c.ShouldBindJSON(&request); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}
	
	err := h.userService.CreateUser(
		request.UserID,
		request.FirstName,
		request.LastName,
		request.Username,
	)
	
	if err != nil {
		h.logger.Error("Failed to create user", "error", err, "user_id", request.UserID)
		
		if err.Error() == "user already exists" {
			c.JSON(http.StatusConflict, gin.H{"error": "User already exists"})
			return
		}
		
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create user"})
		return
	}
	
	c.JSON(http.StatusCreated, gin.H{"status": "User created"})
}
