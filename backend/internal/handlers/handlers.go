package handlers

import (
	"backend/internal/models"
	"database/sql"
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
)

// Generate VPN-key and save it in DB
func GenerateKey(c *gin.Context) {
	// Get user_id from request
	userID := c.PostForm("user_id")
	if userID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "user_id is required"})
		return
	}

	// Placeholder - await for Outline API
	keyValue := "vpn-key-" + userID
	expires := time.Now().Add(7 * 24 * time.Hour).Format(time.RFC3339) // Key for 7 days

	// Save to DB
	db := c.MustGet("db").(*sql.DB) // Getting DB from context (add later in main.go)
	_, err := db.Exec("INSERT INTO vpn_keys (key_value, expires, user_id) VALUES ($1, $2, $3)",
		keyValue, expires, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Return answer
	c.JSON(http.StatusOK, models.VPNKey{
		KeyValue: keyValue,
		Expires:  expires,
		UserID:   userID,
	})
}

// ADD CREATE USER!!!

// Deposit - Incease users balance
func Deposit(c *gin.Context) {
	userID := c.PostForm("user_id")
	amountStr := c.PostForm("amount")
	if userID == "" || amountStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "user_id and amount are required"})
		return
	}

	amount, err := strconv.Atoi(amountStr)
	if err != nil || amount <= 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid amount"})
		return
	}

	db := c.MustGet("db").(*sql.DB)
	_, err = db.Exec("INSERT INTO users (user_id, balance) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET balance = users.balance + $2", userID, amount)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "balance updated", "user_id": userID, "amount": amount})
}

// Withdraw - Decrease users balance
func Withdraw(c *gin.Context) {
	userID := c.PostForm("user_id")
	amountStr := c.PostForm("amount")
	if userID == "" || amountStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "user_id and amount are required"})
		return
	}

	amount, err := strconv.Atoi(amountStr)
	if err != nil || amount <= 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid amount"})
		return
	}

	db := c.MustGet("db").(*sql.DB)
	var balance int
	err = db.QueryRow("SELECT balance FROM users WHERE user_id = $1", userID).Scan(&balance)
	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"error": "user not found"})
		return
	} else if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	if balance < amount {
		c.JSON(http.StatusBadRequest, gin.H{"error": "insufficient balance"})
		return
	}

	_, err = db.Exec("UPDATE users SET balance = balance - $1 WHERE user_id = $2", amount, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "balance withdrawn", "user_id": userID, "amount": amount})
}

// Getting info about User
func GetUser(c *gin.Context) {
	userID := c.Query("user_id")
	if userID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "user_id is required"})
		return
	}

	db := c.MustGet("db").(*sql.DB)
	var user models.User
	err := db.QueryRow("SELECT user_id, balance, subscription_active, subscription_expires, referrals_count, referred_by FROM users WHERE user_id = $1", userID).
		Scan(&user.UserID, &user.Balance, &user.SubscriptionActive, &user.SubscriptionExpires, &user.ReferralsCount, &user.ReferredBy)
	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"error": "user not found"})
		return
	} else if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, user)
}

// Activating Subscription
func ActivateSubscription(c *gin.Context) {
	userID := c.PostForm("user_id")
	cost := 300 // PLACEHOLDER
	if userID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "user_id is required"})
		return
	}

	db := c.MustGet("db").(*sql.DB)
	var balance int
	err := db.QueryRow("SELECT balance FROM users WHERE user_id = $1", userID).Scan(&balance)
	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"error": "user not found"})
		return
	} else if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "insufficient balance"}) // CAN BUY NOT FOR BALANCE, DIRECT BUY
		return
	}

	if balance < cost {
		c.JSON(http.StatusBadRequest, gin.H{"error": "insufficient balance"})
		return
	}

	expires := time.Now().Add(30 * 24 * time.Hour).Format(time.RFC3339) // 30 days
	_, err = db.Exec("UPDATE users SET balance = balance - $1, subscription_active = TRUE, subscription_expires = $2 WHERE user_id = $3", cost, expires, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "subscription activated", "expires": expires})
}

// Add referral and bonus
func AddReferral(c *gin.Context) {
	userID := c.PostForm("user_id")
	referredID := c.PostForm("referred_id")
	if userID == "" || referredID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "user_id and referred_id are required"})
		return
	}

	if userID == referredID {
		c.JSON(http.StatusBadRequest, gin.H{"error": "cannot refer yourself"})
		return
	}

	db := c.MustGet("db").(*sql.DB)

	// Check - referred_id is not registred and hasnt referral
	var exists bool
	err := db.QueryRow("SELECT EXISTS(SELECT 1 FROM users WHERE user_id = $1 AND referred_by IS NOT NULL)", referredID).Scan(&exists)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "user already referred"})
		return
	}

	// Add new user and give bonus
	_, err = db.Exec("INSERT INTO users (user_id, referred_by) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET referred_by = $2", referredID, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	_, err = db.Exec("UPDATE users SET balance = balance + 75, referrals_count = referrals_count + 1 WHERE user_id = $1", userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "referral added", "bonus": 75})
}
