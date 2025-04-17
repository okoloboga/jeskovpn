// internal/models/subscription.go
package models

import (
	"time"
)

// Subscription represents a user's subscription
type Subscription struct {
	ID        int       `gorm:"primaryKey" json:"id"`
	UserID    int       `json:"user_id"`
	Type      string    `json:"type"` // device, router, combo
	Duration  int       `json:"duration"`
	ComboType int       `json:"combo_type"`
	CreatedAt time.Time `json:"created_at"`
	// ExpiresAt removed as per your requirement
}
