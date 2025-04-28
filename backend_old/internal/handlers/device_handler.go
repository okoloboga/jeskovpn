// internal/handlers/device_handler.go
package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/okoloboga/jeskovpn/backend/internal/services"
	"github.com/okoloboga/jeskovpn/backend/pkg/logger"
)

// DeviceHandler handles device-related requests
type DeviceHandler struct {
	deviceService services.DeviceService
	logger        logger.Logger
}

// NewDeviceHandler creates a new device handler
func NewDeviceHandler(deviceService services.DeviceService, logger logger.Logger) *DeviceHandler {
	return &DeviceHandler{
		deviceService: deviceService,
		logger:        logger,
	}
}

// GenerateKey handles POST /devices/key
func (h *DeviceHandler) GenerateKey(c *gin.Context) {
	// Parse request body
	var request struct {
		UserID int    `json:"user_id" binding:"required"`
		Device string `json:"device" binding:"required"`
		Slot   string `json:"slot" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid request body", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	// Generate key
	key, err := h.deviceService.GenerateKey(request.UserID, request.Device, request.Slot)
	if err != nil {
		h.logger.Error("Failed to generate key", map[string]interface{}{
			"error":   err.Error(),
			"user_id": request.UserID,
			"device":  request.Device,
			"slot":    request.Slot,
		})

		if err.Error() == "no active subscription" {
			c.JSON(http.StatusForbidden, gin.H{"error": "No active subscription"})
			return
		}

		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate key"})
		return
	}

	h.logger.Info("Key generated", map[string]interface{}{
		"user_id": request.UserID,
		"device":  request.Device,
		"slot":	   request.Slot,
	})

	c.JSON(http.StatusOK, gin.H{"key": key})
}

// GetKey handles GET /devices/key
func (h* DeviceHandler) GetKey(c *gin.Context) {
	// Parse request body
	var request struct {
		UserID int 	  `json:"user_id" binding:"required"`
		DeviceName string `json:"device" binding:"required"`
	}
	
	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid request body", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	// Get device key from Service 
	device, err := h.deviceService.GetKey(request.UserID, request.DeviceName)
	if err != nil {
		h.logger.Error("Failed to get Device Key", map[string]interface{}{
			"error": err.Error(), 
			"user_id": request.UserID,
			"device_name":  request.DeviceName,
		})
	}

	h.logger.Info("VPN key retrieved", map[string]interface{}{
        "user_id":    request.UserID,
        "device_name": request.DeviceName,
		"device_key": device,
    })

    c.JSON(http.StatusOK, gin.H{"key": device})
}

// RevokeKey handles DELETE /devices/key
func (h *DeviceHandler) RevokeKey(c *gin.Context) {
	// Parse request body
	var request struct {
		UserID int    `json:"user_id" binding:"required"`
		Device string `json:"device" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid request body", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	// Remove device
	err := h.deviceService.RemoveDevice(request.UserID, request.Device)
	if err != nil {
		h.logger.Error("Failed to remove device", map[string]interface{}{
			"error":   err.Error(),
			"user_id": request.UserID,
			"device":  request.Device,
		})

		if err.Error() == "device not found" {
			c.JSON(http.StatusNotFound, gin.H{"error": "Device not found"})
			return
		}

		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to remove device"})
		return
	}

	h.logger.Info("Device removed", map[string]interface{}{
		"user_id": request.UserID,
		"device":  request.Device,
	})

	c.JSON(http.StatusOK, gin.H{"status": "Device removed"})
}
