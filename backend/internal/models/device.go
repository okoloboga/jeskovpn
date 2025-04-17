package models

import (
	"time"
)

// internal/models/device.go
type Device struct {
	ID             int       `gorm:"primaryKey" json:"id"`
	UserID         int       `json:"user_id"`
	SubscriptionID int       `json:"subscription_id"`
	DeviceName     string    `json:"device_name"`
	VpnKey         string    `json:"vpn_key"`        // Access URL for the client
	OutlineKeyID   string    `json:"outline_key_id"` // ID of the key in Outline server
	CreatedAt      time.Time `json:"created_at"`
}
