package handlers

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/okoloboga/jeskovpn/backend/internal/services"
	"github.com/okoloboga/jeskovpn/backend/pkg/logger"
)

// TicketHandler handles ticket-related requests
type TicketHandler struct {
	ticketService services.TicketService
	logger        logger.Logger
}

// NewTicketHandler creates a new ticket handler
func NewTicketHandler(ticketService services.TicketService, logger logger.Logger) *TicketHandler {
	return &TicketHandler{
		ticketService: ticketService,
		logger:        logger,
	}
}

// CreateTicket handles POST /tickets
func (h *TicketHandler) CreateTicket(c *gin.Context) {
	// Parse request body
	var request struct {
		UserID   int    `json:"user_id" binding:"required"`
		Username string `json:"username" binding:"required"`
		Content  string `json:"content" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid request body", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	// Create ticket
	err := h.ticketService.CreateTicket(request.UserID, request.Username, request.Content)
	if err != nil {
		h.logger.Error("Failed to create ticket", map[string]interface{}{
			"error":    err.Error(),
			"user_id":  request.UserID,
			"username": request.Username,
		})
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create ticket"})
		return
	}

	h.logger.Info("Ticket created", map[string]interface{}{
		"user_id":  request.UserID,
		"username": request.Username,
	})

	c.JSON(http.StatusCreated, gin.H{"status": "Ticket created"})
}

// GetTicket handles GET /tickets/:user_id
func (h *TicketHandler) GetTicket(c *gin.Context) {
	// Parse user_id from URL
	userID, err := strconv.Atoi(c.Param("user_id"))
	if err != nil {
		h.logger.Error("Invalid user_id format")
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id"})
		return
	}

	// Get ticket
	ticket, err := h.ticketService.GetTicket(userID)
	if err != nil {
		h.logger.Error("Failed to get ticket", map[string]interface{}{
			"error":   err.Error(),
			"user_id": userID,
		})
		c.JSON(http.StatusNotFound, gin.H{"error": "Ticket not found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"user_id":    ticket.UserID,
		"content":    ticket.Content,
		"created_at": ticket.CreatedAt,
	})
}

// DeleteTicket handles DELETE /tickets/:user_id
func (h *TicketHandler) DeleteTicket(c *gin.Context) {
	// Parse user_id from URL
	userID, err := strconv.Atoi(c.Param("user_id"))
	if err != nil {
		h.logger.Error("Invalid user_id format")
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id"})
		return
	}

	// Delete ticket
	err = h.ticketService.DeleteTicket(userID)
	if err != nil {
		h.logger.Error("Failed to delete ticket", map[string]interface{}{
			"error":   err.Error(),
			"user_id": userID,
		})

		if err.Error() == "ticket not found" {
			c.JSON(http.StatusNotFound, gin.H{"error": "Ticket not found"})
			return
		}

		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete ticket"})
		return
	}

	h.logger.Info("Ticket deleted", map[string]interface{}{"user_id": userID})
	c.JSON(http.StatusOK, gin.H{"status": "Ticket deleted"})
}
