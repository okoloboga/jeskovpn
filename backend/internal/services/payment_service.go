package services

import (
	"errors"
	"time"

	"github.com/google/uuid"
	"github.com/okoloboga/jeskovpn/backend/internal/models"
	"github.com/okoloboga/jeskovpn/backend/internal/repositories"
)

// PaymentService defines methods for payment-related operations
type PaymentService interface {
	InitiateDeposit(userID int, amount float64, period int, DeviceType string, paymentType string) (string, error)
	ProcessPayment(paymentID string, status string) error
	ProcessBalancePayment(userID int, amount float64, period int, deviceType string, paymentType string) error
	ProcessWebhookPayment(userID int, amount float64, period int, deviceType string, paymentType string, paymentID, status string) error
}

// paymentService implements PaymentService
type paymentService struct {
	paymentRepo repositories.PaymentRepository
	userRepo    repositories.UserRepository
}

// NewPaymentService creates a new payment service
func NewPaymentService(
	paymentRepo repositories.PaymentRepository,
	userRepo repositories.UserRepository,
) PaymentService {
	return &paymentService{
		paymentRepo: paymentRepo,
		userRepo:    userRepo,
	}
}

// InitiateDeposit initiates a deposit payment
func (s *paymentService) InitiateDeposit(userID int, amount float64, period int, deviceType string, paymentType string) (string, error) {
	// Check if user exists
	_, err := s.userRepo.GetByID(userID)
	if err != nil {
		return "", errors.New("user not found")
	}

	// Generate a unique payment ID
	paymentID := "pay_" + uuid.New().String()

	// Create a pending payment
	payment := &models.Payment{
		UserID:      userID,
		Amount:      amount,
		Period:      period,
		DeviceType:  deviceType,
		PaymentType: paymentType,
		Status:      "pending",
		PaymentID:   paymentID,
		CreatedAt:   time.Now(),
	}

	if err := s.paymentRepo.Create(payment); err != nil {
		return "", err
	}

	return paymentID, nil
}

// ProcessPayment processes a payment callback/webhook (legacy)
func (s *paymentService) ProcessPayment(paymentID string, status string) error {
	// Get the payment
	payment, err := s.paymentRepo.GetByPaymentID(paymentID)
	if err != nil {
		return err
	}

	// Update payment status
	if err := s.paymentRepo.UpdateStatus(paymentID, status); err != nil {
		return err
	}

	// If payment was successful, update user's balance
	if status == "succeeded" {
		return s.userRepo.UpdateBalance(payment.UserID, payment.Amount)
	}

	return nil
}

// ProcessBalancePayment processes a payment from user's balance
func (s *paymentService) ProcessBalancePayment(userID int, amount float64, period int, deviceType string, paymentType string) error {
	// Get the user to check balance
	user, err := s.userRepo.GetByID(userID)
	if err != nil {
		return errors.New("user not found")
	}

	// Check if user has enough balance
	if user.Balance < amount {
		return errors.New("insufficient balance")
	}

	// Deduct from user's balance
	if err := s.userRepo.UpdateBalance(userID, -amount); err != nil {
		return err
	}

	// Create a payment record
	payment := &models.Payment{
		UserID:      userID,
		Amount:      amount,
		Period:      period,
		PaymentType: paymentType,
		Status:      "succeeded",
		PaymentID:   "balance_" + uuid.New().String(),
		CreatedAt:   time.Now(),
	}

	if err := s.paymentRepo.Create(payment); err != nil {
		// Refund the balance
		_ = s.userRepo.UpdateBalance(userID, amount)
		return err
	}

	// Update subscription duration
	switch paymentType {
	case "device_subscription":
		user.Subscription.Device.Duration = period
	case "router_subscription":
		user.Subscription.Router.Duration = period
	case "combo_subscription":
		user.Subscription.Combo.Duration = period
	default:
		return errors.New("unknown payment type")
	}

	// Save the updated user
	if err := s.userRepo.Update(user); err != nil {
		return err
	}

	return nil
}

// ProcessWebhookPayment processes a payment from external webhook (Ukassa, CryptoBot)
func (s *paymentService) ProcessWebhookPayment(userID int, amount float64, period int, deviceType string, paymentType, paymentID, status string) error {
	// Check if user exists
	user, err := s.userRepo.GetByID(userID)
	if err != nil {
		return errors.New("user not found")
	}

	// Check if payment already exists
	existingPayment, _ := s.paymentRepo.GetByPaymentID(paymentID)
	if existingPayment != nil {
		// Update status if payment exists
		if err := s.paymentRepo.UpdateStatus(paymentID, status); err != nil {
			return err
		}
	} else {
		// Create new payment record
		payment := &models.Payment{
			UserID:      userID,
			Amount:      amount,
			Period:      period,
			PaymentType: paymentType,
			Status:      status,
			PaymentID:   paymentID,
			CreatedAt:   time.Now(),
		}
		if err := s.paymentRepo.Create(payment); err != nil {
			return err
		}
	}

	// If payment is successful, update balance and subscription
	if status == "succeeded" || status == "invoice_paid" {
		// Add to balance
		if err := s.userRepo.UpdateBalance(userID, amount); err != nil {
			return err
		}

		// Update subscription duration
		switch paymentType {
		case "device_subscription":
			user.Subscription.Device.Duration = period
		case "router_subscription":
			user.Subscription.Router.Duration = period
		case "combo_subscription":
			user.Subscription.Combo.Duration = period
		default:
			return errors.New("unknown payment type")
		}

		// Save updated user
		if err := s.userRepo.Update(user); err != nil {
			return err
		}
	}

	return nil
}
