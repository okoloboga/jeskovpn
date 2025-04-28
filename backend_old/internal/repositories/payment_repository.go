package repositories

import (
	"errors"

	"github.com/okoloboga/jeskovpn/backend/internal/models"
	"gorm.io/gorm"
)

// PaymentRepository defines methods for payment data access
type PaymentRepository interface {
	Create(payment *models.Payment) error
	GetByPaymentID(paymentID string) (*models.Payment, error)
	UpdateStatus(paymentID string, status string) error
	GetByUserID(userID int) ([]models.Payment, error)
}

// paymentRepository implements PaymentRepository
type paymentRepository struct {
	db *gorm.DB
}

// NewPaymentRepository creates a new payment repository
func NewTransactionRepository(db *gorm.DB) PaymentRepository {
	return &paymentRepository{db: db}
}

// Create adds a new payment
func (r *paymentRepository) Create(payment *models.Payment) error {
	return r.db.Create(payment).Error
}

// GetByPaymentID retrieves a paymentby payment ID
func (r *paymentRepository) GetByPaymentID(paymentID string) (*models.Payment, error) {
	var payment models.Payment
	result := r.db.Where("payment_id = ?", paymentID).First(&payment)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, errors.New("payment not found")
		}
		return nil, result.Error
	}
	return &payment, nil
}

// UpdateStatus updates a payment's status
func (r *paymentRepository) UpdateStatus(paymentID string, status string) error {
	result := r.db.Model(&models.Payment{}).
		Where("payment_id = ?", paymentID).
		Update("status", status)

	if result.Error != nil {
		return result.Error
	}

	if result.RowsAffected == 0 {
		return errors.New("payment not found")
	}

	return nil
}

// GetByUserID retrieves all transactions for a user
func (r *paymentRepository) GetByUserID(userID int) ([]models.Payment, error) {
	var transactions []models.Payment
	result := r.db.Where("user_id = ?", userID).
		Order("created_at DESC").
		Find(&transactions)

	if result.Error != nil {
		return nil, result.Error
	}

	return transactions, nil
}
