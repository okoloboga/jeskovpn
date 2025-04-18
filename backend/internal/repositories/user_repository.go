package repositories

import (
	"errors"
	"fmt"

	"github.com/okoloboga/jeskovpn/backend/internal/models"

	"gorm.io/gorm"
)

// UserRepository defines methods for user data access
type UserRepository interface {
	GetByID(userID int) (*models.User, error)
	Create(user *models.User) error
	Update(user *models.User) error
	UpdateBalance(userID int, amount float64) error
	Exists(userID int) (bool, error)
	CreateDevice(device *models.DeviceSubscription) error
	CreateRouter(device *models.RouterSubscription) error
	CreateCombo(device *models.ComboSubscription) error
}

// userRepository implements UserRepository
type userRepository struct {
	db *gorm.DB
}

// NewUserRepository creates a new user repository
func NewUserRepository(db *gorm.DB) UserRepository {
	return &userRepository{db: db}
}

// GetByID retrieves a user by ID
func (r *userRepository) GetByID(userID int) (*models.User, error) {
	var user models.User
	result := r.db.First(&user, userID)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, errors.New("user not found")
		}
		return nil, result.Error
	}
	return &user, nil
}

// Create adds a new user
func (r *userRepository) Create(user *models.User) error {
	return r.db.Create(user).Error
}

func (r *userRepository) Update(user *models.User) error {
	return r.db.Save(user).Error
}

// UpdateBalance updates a user's balance
func (r *userRepository) UpdateBalance(userID int, amount float64) error {
	result := r.db.Model(&models.User{}).
		Where("user_id = ?", userID).
		Update("balance", gorm.Expr("balance + ?", amount))
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return errors.New("user not found")
	}
	return nil
}

// Exists checks if a user exists
func (r *userRepository) Exists(userID int) (bool, error) {
	var count int64
	err := r.db.Model(&models.User{}).Where("user_id = ?", userID).Count(&count).Error
	if err != nil {
		return false, fmt.Errorf("failed to check user existence: %w", err)
	}
	return count > 0, nil
}

// Create adds a new device
func (r *userRepository) CreateDevice(device *models.DeviceSubscription) error {
	return r.db.Create(device).Error
}

// Create adds a new router
func (r *userRepository) CreateRouter(device *models.RouterSubscription) error {
	return r.db.Create(device).Error
}

// Create adds a new combo
func (r *userRepository) CreateCombo(device *models.ComboSubscription) error {
	return r.db.Create(device).Error
}
