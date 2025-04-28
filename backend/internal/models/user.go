package models

import (
	"database/sql/driver"
	"encoding/json"
	"fmt"
	"time"
)

type User struct {
	UserID       int                    `gorm:"primaryKey;column:user_id" json:"user_id"`
	FirstName    string                 `gorm:"column:first_name" json:"first_name"`
	LastName     string                 `gorm:"column:last_name" json:"last_name"`
	Username     string                 `gorm:"column:username" json:"username"`
	Balance      float64                `gorm:"column:balance" json:"balance"`
	CreatedAt    time.Time              `gorm:"column:created_at" json:"created_at"`
	Subscription SubscriptionCollection `gorm:"type:json;column:subscription" json:"subscription"`
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
	Devices  []string `json:"devices"`
	Duration int 	  `json:"duration"`
}

type ComboSubscription struct {
	Devices  []string `json:"devices"`
	Duration int      `json:"duration"`
	Type     int      `json:"type"`
}

// Value implements the driver.Valuer interface for JSON serialization
func (s SubscriptionCollection) Value() (driver.Value, error) {
	return json.Marshal(s)
}

// Scan implements the sql.Scanner interface for JSON deserialization
func (s *SubscriptionCollection) Scan(value interface{}) error {
	if value == nil {
		*s = SubscriptionCollection{}
		return nil
	}
	bytes, ok := value.([]byte)
	if !ok {
		return fmt.Errorf("failed to unmarshal JSONB value: %v", value)
	}
	return json.Unmarshal(bytes, s)
}
