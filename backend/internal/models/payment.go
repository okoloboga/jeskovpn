package models

import (
	"time"
)

// Payment представляет финансовую транзакцию
type Payment struct {
	ID          int       `gorm:"primaryKey" json:"id"`
	UserID      int       `json:"user_id"`
	Amount      float64   `json:"amount"`
	Period      int       `json:"period"`
	DeviceType  string    `json:"device_type"`
	PaymentType string    `json:"payment_type"` // ukassa, crypto, balance
	Status      string    `json:"status"`       // pending, succeeded, failed
	PaymentID   string    `json:"payment_id"`
	CreatedAt   time.Time `json:"created_at"`
}
