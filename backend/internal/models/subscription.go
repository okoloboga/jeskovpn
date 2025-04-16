package models

import (
	"time"
)

// Subscription представляет подписку пользователя
type Subscription struct {
	ID        int       `gorm:"primaryKey" json:"id"`
	UserID    int       `json:"user_id"`
	Type      string    `json:"type"` // device, router, combo
	Duration  int       `json:"duration"`
	ComboType int       `json:"combo_type"`
	ExpiresAt time.Time `json:"expires_at"`
}
