package db

import (
	"backend/internal/config"
	"database/sql"
	"fmt"

	_ "github.com/lib/pq"
)

// Init Database connection and create tables
func InitDB(cfg config.Config) (*sql.DB, error) {
	// Connection string
	connStr := fmt.Sprintf("host=%s user=%s password=%s dbname=%s port=%s sslmode=disable",
		cfg.DBHost, cfg.DBUser, cfg.DBPassword, cfg.DBName, cfg.DBPort)

	// Open connection
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return nil, err
	}

	// Check connect
	err = db.Ping()
	if err != nil {
		return nil, err
	}

	// Create table vpn_keys
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS vpn_keys (
			id SERIAL PRIMARY KEY,
			key_value TEXT NOT NULL,
			expires TIMESTAMP NOT NULL,
			user_id TEXT NOT NULL
		)
	`)
	if err != nil {
		return nil, err
	}

	// Create table users
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS users (
			user_id TEXT PRIMARY KEY,
			balance INTEGER NOT NULL DEFAULT 0,
			subscription_active BOOLEAN NOT NULL DEFAULT FALSE,
			subscription_expires TIMESTAMP,
			referrals_count INTEGER NOT NULL DEFAULT 0,
			reffered_by TEXT
		)
	`)
	if err != nil {
		return nil, err
	}

	return db, nil
}
