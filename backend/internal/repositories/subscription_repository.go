package repositories

import (
	"errors"

	"github.com/yourusername/backend/internal/models"
	"gorm.io/gorm"
)

// SubscriptionRepository defines methods for subscription data access
type SubscriptionRepository interface {
	GetByUserID(userID int, subscriptionType string) (*models.Subscription, error)
	Create(subscription *models.Subscription) error
	Update(subscription *models.Subscription) error
	UpdateDuration(id int, duration int) error
}

// subscriptionRepository implements SubscriptionRepository
type subscriptionRepository struct {
	db *gorm.DB
}

// NewSubscriptionRepository creates a new subscription repository
func NewSubscriptionRepository(db *gorm.DB) SubscriptionRepository {
	return &subscriptionRepository{db: db}
}

// GetByUserID retrieves a subscription by user ID and type
func (r *subscriptionRepository) GetByUserID(userID int, subscriptionType string) (*models.Subscription, error) {
	var subscription models.Subscription
	result := r.db.Where("user_id = ? AND type = ?", userID, subscriptionType).First(&subscription)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, errors.New("subscription not found")
		}
		return nil, result.Error
	}
	return &subscription, nil
}

// Create adds a new subscription
func (r *subscriptionRepository) Create(subscription *models.Subscription) error {
	return r.db.Create(subscription).Error
}

// Update updates an existing subscription
func (r *subscriptionRepository) Update(subscription *models.Subscription) error {
	return r.db.Save(subscription).Error
}

// UpdateDuration updates the duration of a subscription
func (r *subscriptionRepository) UpdateDuration(id int, duration int) error {
	result := r.db.Model(&models.Subscription{}).
		Where("id = ?", id).
		Update("duration", gorm.Expr("duration + ?", duration))

	if result.Error != nil {
		return result.Error
	}

	if result.RowsAffected == 0 {
		return errors.New("subscription not found")
	}

	return nil
}
