package models

import (
	"time"
)

// Device представляет устройство пользователя
type Device struct {
	ID             int       `gorm:"primaryKey" json:"id"`
	UserID         int       `json:"user_id"`
	SubscriptionID int       `json:"subscription_id"`
	DeviceName     string    `json:"device_name"`
	VpnKey         string    `json:"vpn_key"`
	CreatedAt      time.Time `json:"created_at"`
}
