// internal/services/device_service.go
package services

import (
	"errors"
	"time"
	"fmt"

	"github.com/okoloboga/jeskovpn/backend/internal/models"
	"github.com/okoloboga/jeskovpn/backend/internal/repositories"
	"github.com/okoloboga/jeskovpn/backend/pkg/vpn"
)

// DeviceService defines methods for device-related operations
type DeviceService interface {
	GenerateKey(userID int, deviceName string, slot string) (string, error)
	RemoveDevice(userID int, deviceName string) error
	GetDevices(userID int) ([]string, error)
	GetKey(userID int, deviceName string) (string, error)
}

// deviceService implements DeviceService
type deviceService struct {
	deviceRepo   repositories.DeviceRepository
	userRepo     repositories.UserRepository
	vpnGenerator vpn.KeyGenerator
}

// NewDeviceService creates a new device service
func NewDeviceService(
	deviceRepo repositories.DeviceRepository,
	userRepo repositories.UserRepository,
	vpnGenerator vpn.KeyGenerator,
) DeviceService {
	return &deviceService{
		deviceRepo:   deviceRepo,
		userRepo:     userRepo,
		vpnGenerator: vpnGenerator,
	}
}

// GenerateKey generates a VPN key for a device
func (s *deviceService) GenerateKey(userID int, deviceName string, slot string) (string, error) {
	// Slot validation
	if slot != "device" && slot != "router" && slot != "combo" {
		return "", fmt.Errorf("invalid slot: %s", slot)
	}

	// Check if user has an active device subscription
	user, err := s.userRepo.GetByID(userID)
	if err != nil {
		return "", fmt.Errorf("failed to get user: %w", err)
	}

	var duration int

	if deviceName == "device" {
		duration = user.Subscription.Device.Duration
	} else if deviceName == "router" {
		duration = user.Subscription.Router.Duration
	} else if deviceName == "combo" {
		duration = user.Subscription.Combo.Duration
	}

	if duration <= 0 {
		return "", errors.New("no active subscription")
	}

	// Check if device already exists
	existingDevice, err := s.deviceRepo.GetByUserIDAndName(userID, deviceName)
	if err == nil && existingDevice != nil {
		// Device already exists, return existing key
		return existingDevice.VpnKey, nil
	}

	// Generate a new VPN key
	vpnKey, err := s.vpnGenerator.GenerateKey(userID, deviceName)
	if err != nil {
		return "", err
	}

	// Create a new device record
	device := &models.Device{
		UserID:     userID,
		DeviceName: deviceName,
		VpnKey:     vpnKey,
		CreatedAt:  time.Now(),
	}

	if err := s.deviceRepo.Create(device); err != nil {
		// Try to revoke the key if we failed to save it
		_ = s.vpnGenerator.RevokeKey(userID, deviceName)
		return "", fmt.Errorf("failed to create device: %w", err)
	}

	switch slot {
    case "device":
        user.Subscription.Device.Devices = append(user.Subscription.Device.Devices, deviceName)
    case "router":
        user.Subscription.Router.Devices = append(user.Subscription.Router.Devices, deviceName)
    case "combo":
        user.Subscription.Combo.Devices = append(user.Subscription.Combo.Devices, deviceName)
    }

    // Save updated user
    if err := s.userRepo.Update(user); err != nil {
        _ = s.deviceRepo.Delete(userID, deviceName)
        _ = s.vpnGenerator.RevokeKey(userID, deviceName)
        return "", fmt.Errorf("failed to update user subscription: %w", err)
    }

	return vpnKey, nil
}

// RemoveDevice removes a device
func (s *deviceService) RemoveDevice(userID int, deviceName string) error {
	// Get the device to ensure it exists
	_, err := s.deviceRepo.GetByUserIDAndName(userID, deviceName)
	if err != nil {
		return err
	}

	// Revoke the VPN key
	if err := s.vpnGenerator.RevokeKey(userID, deviceName); err != nil {
		return err
	}

	// Delete the device from the database
	return s.deviceRepo.Delete(userID, deviceName)
}

// GetDevices retrieves all devices for a user
func (s *deviceService) GetDevices(userID int) ([]string, error) {
	devices, err := s.deviceRepo.GetAllByUserID(userID)
	if err != nil {
		return nil, err
	}

	deviceNames := make([]string, len(devices))
	for i, device := range devices {
		deviceNames[i] = device.DeviceName
	}

	return deviceNames, nil
}

// GetKey get Device key for User 
func (s *deviceService) GetKey(userID int, deviceName string) (string, error) {
	device, err := s.deviceRepo.GetByUserIDAndName(userID, deviceName)
	if err != nil {
		return "Error in GetKey", err 
	}
	
	return device.VpnKey, nil
}
