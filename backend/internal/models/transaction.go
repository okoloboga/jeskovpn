package models

import (
	"time"
)

// Transaction представляет финансовую транзакцию
type Transaction struct {
	ID          int       `gorm:"primaryKey" json:"id"`
	UserID      int       `json:"user_id"`
	Amount      float64   `json:"amount"`
	PaymentType string    `json:"payment_type"` // ukassa, crypto, balance, stars
	Status      string    `json:"status"`       // pending, succeeded, failed
	PaymentID   string    `json:"payment_id"`
	CreatedAt   time.Time `json:"created_at"`
}
