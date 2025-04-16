package vpn

// KeyGenerator представляет интерфейс для генерации VPN-ключей
type KeyGenerator interface {
	GenerateKey(userID int, device string) (string, error)
	RevokeKey(userID int, device string) error
}
