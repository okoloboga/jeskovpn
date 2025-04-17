package services

import (
	"errors"
	"time"

	"github.com/okoloboga/jeskovpn/backend/internal/models"
	"github.com/okoloboga/jeskovpn/backend/internal/repositories"
)

// PaymentService defines methods for payment-related operations
type PaymentService interface {
	InitiateDeposit(userID int, amount float64, paymentType string) (string, error)
	ProcessPayment(paymentID string, status string) error
	ProcessBalancePayment(userID int, amount float64, paymentType string) error
}

// paymentService implements PaymentService
type paymentService struct {
	transactionRepo  repositories.TransactionRepository
	userRepo         repositories.UserRepository
	subscriptionRepo repositories.SubscriptionRepository
}

// NewPaymentService creates a new payment service
func NewPaymentService(
	transactionRepo repositories.TransactionRepository,
	userRepo repositories.UserRepository,
	subscriptionRepo repositories.SubscriptionRepository,
) PaymentService {
	return &paymentService{
		transactionRepo:  transactionRepo,
		userRepo:         userRepo,
		subscriptionRepo: subscriptionRepo,
	}
}

// InitiateDeposit initiates a deposit transaction
func (s *paymentService) InitiateDeposit(userID int, amount float64, paymentType string) (string, error) {
	// Check if user exists
	_, err := s.userRepo.GetByID(userID)
	if err != nil {
		return "", errors.New("user not found")
	}

	// Generate a unique payment ID (in a real app, this would be more sophisticated)
	paymentID := "pay_" + time.Now().Format("20060102150405")

	// Create a pending transaction
	transaction := &models.Transaction{
		UserID:      userID,
		Amount:      amount,
		PaymentType: paymentType,
		Status:      "pending",
		PaymentID:   paymentID,
		CreatedAt:   time.Now(),
	}

	if err := s.transactionRepo.Create(transaction); err != nil {
		return "", err
	}

	// In a real app, you would integrate with the payment provider here
	// and return a payment URL or other payment details

	return paymentID, nil
}

// ProcessPayment processes a payment callback/webhook
func (s *paymentService) ProcessPayment(paymentID string, status string) error {
	// Get the transaction
	transaction, err := s.transactionRepo.GetByPaymentID(paymentID)
	if err != nil {
		return err
	}

	// Update transaction status
	if err := s.transactionRepo.UpdateStatus(paymentID, status); err != nil {
		return err
	}

	// If payment was successful, update user's balance
	if status == "succeeded" {
		return s.userRepo.UpdateBalance(transaction.UserID, transaction.Amount)
	}

	return nil
}

// ProcessBalancePayment processes a payment from user's balance
func (s *paymentService) ProcessBalancePayment(userID int, amount float64, paymentType string) error {
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

	// Create a transaction record
	transaction := &models.Transaction{
		UserID:      userID,
		Amount:      amount,
		PaymentType: paymentType,
		Status:      "succeeded",
		PaymentID:   "balance_" + time.Now().Format("20060102150405"),
		CreatedAt:   time.Now(),
	}

	if err := s.transactionRepo.Create(transaction); err != nil {
		// If we can't create the transaction record, refund the balance
		_ = s.userRepo.UpdateBalance(userID, amount)
		return err
	}

	// Update subscription based on payment type
	// For example, if payment_type is "device_subscription", extend device subscription
	if paymentType == "device_subscription" {
		subscription, err := s.subscriptionRepo.GetByUserID(userID, "device")
		if err != nil {
			return err
		}

		// Extend subscription by 1 month (or whatever period the payment covers)
		return s.subscriptionRepo.UpdateDuration(subscription.ID, 1)
	}

	return nil
}
