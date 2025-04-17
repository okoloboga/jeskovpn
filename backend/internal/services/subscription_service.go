// internal/services/subscription_service.go
package services

import (
	"errors"
	"time"

	"github.com/okoloboga/backend/internal/models"
	"github.com/okoloboga/backend/internal/repositories"
)

// SubscriptionService defines methods for subscription-related operations
type SubscriptionService interface {
	GetSubscription(userID int, subscriptionType string) (*models.Subscription, error)
	ExtendSubscription(userID int, subscriptionType string, duration int) error
	GetUserSubscriptions(userID int) (map[string]interface{}, error)
}

// subscriptionService implements SubscriptionService
type subscriptionService struct {
	subscriptionRepo repositories.SubscriptionRepository
	deviceRepo repositories.DeviceRepository
}

// NewSubscriptionService creates a new subscription service
func NewSubscriptionService(
	subscriptionRepo repositories.SubscriptionRepository,
	deviceRepo repositories.DeviceRepository,
) SubscriptionService {
	return &subscriptionService{
		subscriptionRepo: subscriptionRepo,
		deviceRepo: deviceRepo,
	}
}

// GetSubscription retrieves a subscription by user ID and type
func (s *subscriptionService) GetSubscription(userID int, subscriptionType string) (*models.Subscription, error) {
	return s.subscriptionRepo.GetByUserID(userID, subscriptionType)
}

// ExtendSubscription extends a subscription's duration
func (s *subscriptionService) ExtendSubscription(userID int, subscriptionType string, duration int) error {
	subscription, err := s.subscriptionRepo.GetByUserID(userID, subscriptionType)
	if err != nil {
		return err
	}
	
	return