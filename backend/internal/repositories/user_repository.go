package repositories

import (
	"errors"
	"vpn-bot-backend/internal/models"

	"gorm.io/gorm"
)

// UserRepository defines methods for user data access
type UserRepository interface {
	GetByID(userID int) (*models.User, error)
	Create(user *models.User) error
	UpdateBalance(userID int, amount float64) error
	Exists(userID int) (bool, error)
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
	err := r.db.Model(&models.User{}).
		Where("user_id = ?", userID).
		Count(&count).Error
	return count > 0, err
}
