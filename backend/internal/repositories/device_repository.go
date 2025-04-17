// internal/repositories/device_repository.go
package repositories

import (
	"errors"

	"github.com/yourusername/backend/internal/models"
	"gorm.io/gorm"
)

// DeviceRepository defines methods for device data access
type DeviceRepository interface {
	GetByUserIDAndName(userID int, deviceName string) (*models.Device, error)
	GetAllByUserID(userID int) ([]models.Device, error)
	Create(device *models.Device) error
	Delete(userID int, deviceName string) error
}

// deviceRepository implements DeviceRepository
type deviceRepository struct {
	db *gorm.DB
}

// NewDeviceRepository creates a new device repository
func NewDeviceRepository(db *gorm.DB) DeviceRepository {
	return &deviceRepository{db: db}
}

// GetByUserIDAndName retrieves a device by user ID and device name
func (r *deviceRepository) GetByUserIDAndName(userID int, deviceName string) (*models.Device, error) {
	var device models.Device
	result := r.db.Where("user_id = ? AND device_name = ?", userID, deviceName).First(&device)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, errors.New("device not found")
		}
		return nil, result.Error
	}
	return &device, nil
}

// GetAllByUserID retrieves all devices for a user
func (r *deviceRepository) GetAllByUserID(userID int) ([]models.Device, error) {
	var devices []models.Device
	result := r.db.Where("user_id = ?", userID).Find(&devices)
	if result.Error != nil {
		return nil, result.Error
	}
	return devices, nil
}

// Create adds a new device
func (r *deviceRepository) Create(device *models.Device) error {
	return r.db.Create(device).Error
}

// Delete removes a device
func (r *deviceRepository) Delete(userID int, deviceName string) error {
	result := r.db.Where("user_id = ? AND device_name = ?", userID, deviceName).Delete(&models.Device{})
	if result.Error != nil {
		return result.Error
	}

	if result.RowsAffected == 0 {
		return errors.New("device not found")
	}

	return nil
}
