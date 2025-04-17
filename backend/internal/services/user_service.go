package services

import (
	"errors"
	"time"

	"github.com/services/backend/internal/models"
	"github.com/services/backend/internal/repositories"
)

// UserService defines methods for user-related operations
type UserService interface {
	GetUser(userID int) (*models.User, error)
	CreateUser(userID int, firstName, lastName, username string) error
	UpdateBalance(userID int, amount float64) error
}

// userService implements UserService
type userService struct {
	userRepo         repositories.UserRepository
	subscriptionRepo repositories.SubscriptionRepository
	deviceRepo       repositories.DeviceRepository
}

// NewUserService creates a new user service
func NewUserService(
	userRepo repositories.UserRepository,
	subscriptionRepo repositories.SubscriptionRepository,
	deviceRepo repositories.DeviceRepository,
) UserService {
	return &userService{
		userRepo:         userRepo,
		subscriptionRepo: subscriptionRepo,
		deviceRepo:       deviceRepo,
	}
}

// GetUser retrieves a user with subscription and device information
func (s *userService) GetUser(userID int) (*models.User, error) {
	user, err := s.userRepo.GetByID(userID)
	if err != nil {
		return nil, err
	}

	// Here you would typically fetch subscription and device info
	// and format it according to the expected response

	return user, nil
}

// CreateUser creates a new user
func (s *userService) CreateUser(userID int, firstName, lastName, username string) error {
	// Check if user already exists
	exists, err := s.userRepo.Exists(userID)
	if err != nil {
		return err
	}

	if exists {
		return errors.New("user already exists")
	}

	// Create new user
	user := &models.User{
		UserID:    userID,
		FirstName: firstName,
		LastName:  lastName,
		Username:  username,
		Balance:   0,
		CreatedAt: time.Now(),
	}

	err = s.userRepo.Create(user)
	if err != nil {
		return err
	}

	// Create default subscriptions
	deviceSub := &models.Subscription{
		UserID:    userID,
		Type:      "device",
		Duration:  0,
		ComboType: 0,
		CreatedAt: time.Now(),
	}

	routerSub := &models.Subscription{
		UserID:    userID,
		Type:      "router",
		Duration:  0,
		ComboType: 0,
		CreatedAt: time.Now(),
	}

	comboSub := &models.Subscription{
		UserID:    userID,
		Type:      "combo",
		Duration:  0,
		ComboType: 0,
		CreatedAt: time.Now(),
	}

	if err := s.subscriptionRepo.Create(deviceSub); err != nil {
		return err
	}

	if err := s.subscriptionRepo.Create(routerSub); err != nil {
		return err
	}

	if err := s.subscriptionRepo.Create(comboSub); err != nil {
		return err
	}

	return nil
}

// UpdateBalance updates a user's balance
func (s *userService) UpdateBalance(userID int, amount float64) error {
	return s.userRepo.UpdateBalance(userID, amount)
}
