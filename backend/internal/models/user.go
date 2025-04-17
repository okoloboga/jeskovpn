package models

import (
	"time"
)

type User struct {
	UserID       int                    `gorm:"primaryKey" json:"user_id"`
	FirstName    string                 `json:"first_name"`
	LastName     string                 `json:"last_name"`
	Username     string                 `json:"username"`
	Balance      float64                `json:"balance"`
	CreatedAt    time.Time              `json:"created_at"`
	Subscription SubscriptionCollection `json:"subscription"`
}

type SubscriptionCollection struct {
	Device DeviceSubscription `json:"device"`
	Router RouterSubscription `json:"router"`
	Combo  ComboSubscription  `json:"combo"`
}

type DeviceSubscription struct {
	Devices  []string `json:"devices"`
	Duration int      `json:"duration"`
}

type RouterSubscription struct {
	Duration int `json:"duration"`
}

type ComboSubscription struct {
	Devices  []string `json:"devices"`
	Duration int      `json:"duration"`
	Type     int      `json:"type"`
}
