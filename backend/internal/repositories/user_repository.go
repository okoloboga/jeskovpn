package repositories

import (
	"vpn-bot-backend/internal/models"
	"gorm.io/gorm"
)

// UserRepository представляет репозиторий для работы с пользователями
type UserRepository struct {
	db *gorm.DB
}

// NewUserRepository создает новый репозиторий пользователей
func NewUserRepository(db *gorm.DB) *UserRepository {
	return &UserRepository{db: db}
}

// GetByID получает пользователя по ID
func (r *UserRepository) GetByID(userID int) (*models.User, error) {
	var user models.User
	result := r.db.First(&user, userID)
	return &user, result.Error
}

// Create создает нового пользователя
func (r *UserRepository) Create(user *models.User) error {
	return r.db.Create(user).Error
}

// Update обновляет данные пользователя
func (r *UserRepository) Update(user *models.User) error {
	return r.db.Save(user).Error
}

// Exists проверяет существование пользователя
func (r *UserRepository) Exists(userID int) (bool, error) {
	var count int64
	err := r.db.Model(&models.User{}).Where("user_id = ?", userID).Count(&count).Error
	return count > 0, err
}
