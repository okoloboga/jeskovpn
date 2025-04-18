// internal/services/device_service.go
package services

import (
	"errors"
	"time"

	"github.com/okoloboga/jeskovpn/backend/internal/models"
	"github.com/okoloboga/jeskovpn/backend/internal/repositories"
	"github.com/okoloboga/jeskovpn/backend/pkg/vpn"
)

// DeviceService defines methods for device-related operations
type DeviceService interface {
	GenerateKey(userID int, deviceName string) (string, error)
	RemoveDevice(userID int, deviceName string) error
	GetDevices(userID int) ([]string, error)
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
func (s *deviceService) GenerateKey(userID int, deviceName string) (string, error) {
	// Check if user has an active device subscription
	user, err := s.userRepo.GetByID(userID)
	if err != nil {
		return "", err
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
		return "", err
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
