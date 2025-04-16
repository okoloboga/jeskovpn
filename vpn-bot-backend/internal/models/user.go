package models

import (
	"time"
)

// User представляет пользователя в системе
type User struct {
	UserID    int       `gorm:"primaryKey" json:"user_id"`
	FirstName string    `json:"first_name"`
	LastName  string    `json:"last_name"`
	Username  string    `json:"username"`
	Balance   float64   `json:"balance"`
	CreatedAt time.Time `json:"created_at"`
}

// UserResponse представляет ответ с данными пользователя
type UserResponse struct {
	UserID       int                    `json:"user_id"`
	Balance      float64                `json:"balance"`
	Subscription SubscriptionCollection `json:"subscription"`
}

// SubscriptionCollection представляет коллекцию подписок пользователя
type SubscriptionCollection struct {
	Device DeviceSubscription `json:"device"`
	Router RouterSubscription `json:"router"`
	Combo  ComboSubscription  `json:"combo"`
}

// DeviceSubscription представляет подписку для устройств
type DeviceSubscription struct {
	Devices  []string `json:"devices"`
	Duration int      `json:"duration"`
}

// RouterSubscription представляет подписку для роутеров
type RouterSubscription struct {
	Duration int `json:"duration"`
}

// ComboSubscription представляет комбинированную подписку
type ComboSubscription struct {
	Devices  []string `json:"devices"`
	Duration int      `json:"duration"`
	Type     int      `json:"type"`
}
