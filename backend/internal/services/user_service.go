package services

import (
	"errors"
	"time"
	
	"vpn-bot-backend/internal/models"
	"vpn-bot-backend/internal/repositories"
)

// UserService представляет сервис для работы с пользователями
type UserService struct {
	userRepo        *repositories.UserRepository
	subscriptionRepo *repositories.SubscriptionRepository
	deviceRepo      *repositories.DeviceRepository
}

// NewUserService создает новый сервис пользователей
func NewUserService(
	userRepo *repositories.UserRepository,
	subscriptionRepo *repositories.SubscriptionRepository,
	deviceRepo *repositories.DeviceRepository,
) *UserService {
	return &UserService{
		userRepo:        userRepo,
		subscriptionRepo: subscriptionRepo,
		deviceRepo:      deviceRepo,
	}
}

// GetUser получает данные пользователя с подписками
func (s *UserService) GetUser(userID int) (*models.UserResponse, error) {
	user, err := s.userRepo.GetByID(userID)
	if err != nil {
		return nil, err
	}
	
	// Здесь будет логика получения подписок и устройств
	// Это заглушка, которую нужно будет заменить реальной логикой
	
	return &models.UserResponse{
		UserID:  user.UserID,
		Balance: user.Balance,
		Subscription: models.SubscriptionCollection{
			Device: models.DeviceSubscription{
				Devices:  []string{"android", "iphone"},
				Duration: 3,
			},
			Router: models.RouterSubscription{
				Duration: 0,
			},
			Combo: models.ComboSubscription{
				Devices:  []string{},
				Duration: 0,
				Type:     0,
			},
		},
	}, nil
}

// CreateUser создает нового пользователя
func (s *UserService) CreateUser(userID int, firstName, lastName, username string) error {
	exists, err := s.userRepo.Exists(userID)
	if err != nil {
		return err
	}
	
	if exists {
		return errors.New("user already exists")
	}
	
	user := &models.User{
		UserID:    userID,
		FirstName: firstName,
		LastName:  lastName,
		Username:  username,
		Balance:   0.0,
		CreatedAt: time.Now(),
	}
	
	return s.userRepo.Create(user)
}
