package main

import (
	"backend/internal/config"
	"backend/internal/db"
	"backend/internal/handlers"

	"github.com/gin-gonic/gin"
)

func main() {
	// Load config
	cfg := config.Load()

	// Init Database
	dbConn, err := db.InitDB(cfg)
	if err != nil {
		panic(err)
	}
	defer dbConn.Close()

	// Create Gin router
	r := gin.Default()

	// Bring DB in context of all queries
	r.Use(func(c *gin.Context) {
		c.Set("db", dbConn)
		c.Next()
	})

	// Register endpoints
	r.POST("/generate-key", handlers.GenerateKey)
	r.POST("/deposit", handlers.Deposit)
	r.POST("/withdraw", handlers.Withdraw)
	r.GET("/user", handlers.GetUser)
	r.POST("/activate-subscription", handlers.ActivateSubscription)
	r.POST("/add-referral", handlers.AddReferral)

	// Run server on 8080 port
	r.Run(":8080")
}
