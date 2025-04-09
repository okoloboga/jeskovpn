package models

type VPNKey struct {
	ID       int    `json:"id"`
	KeyValue string `json:"key_value"`
	Expires  string `json:"expires"`
	UserID   string `json:"user_id"`
}

type User struct {
	UserID              string `json:"user_id"`
	Balance             int    `json:"balance"`
	SubscriptionActive  bool   `json:"subscription_active"`
	SubscriptionExpires string `json:"subscription_expires,omitempty"`
	ReferralsCount      int    `json:"referrals_count"`
	ReferredBy          string `json:"referred_by,omitempty"`
}
