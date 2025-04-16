package middleware

import (
	"time"
	
	"github.com/gin-gonic/gin"
	"vpn-bot-backend/pkg/logger"
)

// Logger логирует информацию о запросах
func Logger(log logger.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		
		// Обработка запроса
		c.Next()
		
		// Логирование после обработки
		latency := time.Since(start)
		statusCode := c.Writer.Status()
		clientIP := c.ClientIP()
		method := c.Request.Method
		
		log.Info("Request processed",
			"method", method,
			"path", path,
			"status", statusCode,
			"latency", latency,
			"ip", clientIP,
		)
	}
}
