package vpn

import (
	"fmt"
)

// KeyGenerator представляет интерфейс для генерации VPN-ключей
type KeyGenerator interface {
	GenerateKey(userID int, device string) (string, error)
	RevokeKey(userID int, device string) error
}

type MockKeyGenerator struct{}

func (m *MockKeyGenerator) GenerateKey(userID int, device string) (string, error) {
	return fmt.Sprintf("mock-vpn-key-%d-%s", userID, device), nil
}

func (m *MockKeyGenerator) RevokeKey(userID int, device string) error {
	return nil
}
