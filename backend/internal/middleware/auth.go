package middleware

import (
	"net/http"
	"strings"
	
	"github.com/gin-gonic/gin"
)

// Auth проверяет API-токен в заголовке Authorization
func Auth(apiToken string) gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		
		if authHeader == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Authorization header is required"})
			return
		}
		
		parts := strings.Split(authHeader, " ")
		if len(parts) != 2 || parts[0] != "Bearer" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Authorization header format must be Bearer {token}"})
			return
		}
		
		token := parts[1]
		if token != apiToken {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Invalid API token"})
			return
		}
		
		c.Next()
	}
}
