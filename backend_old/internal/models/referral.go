package models

import (
	"time"
)

// Referral представляет реферальную связь между пользователями
type Referral struct {
	ID         int       `gorm:"primaryKey" json:"id"`
	UserID     int       `json:"user_id"`      // Приглашенный пользователь
	ReferrerID int       `json:"referrer_id"`  // Пригласивший пользователь
	CreatedAt  time.Time `json:"created_at"`
}
