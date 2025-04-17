// internal/repositories/transaction_repository.go
package repositories

import (
	"errors"

	"github.com/okoloboga/jeskovpn/backend/internal/models"
	"gorm.io/gorm"
)

// TransactionRepository defines methods for transaction data access
type TransactionRepository interface {
	Create(transaction *models.Transaction) error
	GetByPaymentID(paymentID string) (*models.Transaction, error)
	UpdateStatus(paymentID string, status string) error
	GetByUserID(userID int) ([]models.Transaction, error)
}

// transactionRepository implements TransactionRepository
type transactionRepository struct {
	db *gorm.DB
}

// NewTransactionRepository creates a new transaction repository
func NewTransactionRepository(db *gorm.DB) TransactionRepository {
	return &transactionRepository{db: db}
}

// Create adds a new transaction
func (r *transactionRepository) Create(transaction *models.Transaction) error {
	return r.db.Create(transaction).Error
}

// GetByPaymentID retrieves a transaction by payment ID
func (r *transactionRepository) GetByPaymentID(paymentID string) (*models.Transaction, error) {
	var transaction models.Transaction
	result := r.db.Where("payment_id = ?", paymentID).First(&transaction)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, errors.New("transaction not found")
		}
		return nil, result.Error
	}
	return &transaction, nil
}

// UpdateStatus updates a transaction's status
func (r *transactionRepository) UpdateStatus(paymentID string, status string) error {
	result := r.db.Model(&models.Transaction{}).
		Where("payment_id = ?", paymentID).
		Update("status", status)

	if result.Error != nil {
		return result.Error
	}

	if result.RowsAffected == 0 {
		return errors.New("transaction not found")
	}

	return nil
}

// GetByUserID retrieves all transactions for a user
func (r *transactionRepository) GetByUserID(userID int) ([]models.Transaction, error) {
	var transactions []models.Transaction
	result := r.db.Where("user_id = ?", userID).
		Order("created_at DESC").
		Find(&transactions)

	if result.Error != nil {
		return nil, result.Error
	}

	return transactions, nil
}
