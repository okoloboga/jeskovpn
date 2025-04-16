package payment

// PaymentProvider представляет интерфейс для платежных систем
type PaymentProvider interface {
	InitiatePayment(userID int, amount float64) (string, error)
	ProcessWebhook(payload []byte) (int, float64, string, error)
}
