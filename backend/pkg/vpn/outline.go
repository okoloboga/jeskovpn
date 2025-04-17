// pkg/vpn/outline.go
package vpn

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
)

// OutlineGenerator generates keys for Outline VPN
type OutlineGenerator struct {
	APIUrl     string // URL to Outline server API
	APIKey     string // API key for authentication
	httpClient *http.Client
}

// NewOutlineGenerator creates a new Outline key generator
func NewOutlineGenerator(apiUrl, apiKey string) KeyGenerator {
	return &OutlineGenerator{
		APIUrl:     apiUrl,
		APIKey:     apiKey,
		httpClient: &http.Client{},
	}
}

// GenerateKey creates a new access key for a device
func (g *OutlineGenerator) GenerateKey(userID int, device string) (string, error) {
	// Create a request to Outline API to generate a new key
	req, err := http.NewRequest("POST", g.APIUrl+"/access-keys", nil)
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Authorization", "Bearer "+g.APIKey)

	resp, err := g.httpClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		return "", fmt.Errorf("API returned non-success status: %d", resp.StatusCode)
	}

	// Parse response to get the access key
	var result struct {
		ID   string `json:"id"`
		Name string `json:"name"`
		Key  string `json:"accessUrl"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", fmt.Errorf("failed to decode response: %w", err)
	}

	// Rename the key to include user and device info
	renameReq, err := http.NewRequest("PUT",
		fmt.Sprintf("%s/access-keys/%s/name", g.APIUrl, result.ID),
		strings.NewReader(fmt.Sprintf(`{"name":"user_%d_%s"}`, userID, device)))
	if err != nil {
		return "", fmt.Errorf("failed to create rename request: %w", err)
	}

	renameReq.Header.Set("Authorization", "Bearer "+g.APIKey)
	renameReq.Header.Set("Content-Type", "application/json")

	_, err = g.httpClient.Do(renameReq)
	if err != nil {
		return "", fmt.Errorf("failed to rename key: %w", err)
	}

	// Store the key ID in our database for future reference
	// This would typically be done in the service layer

	return result.Key, nil
}

// RevokeKey revokes an access key for a device
func (g *OutlineGenerator) RevokeKey(userID int, device string) error {
	// First we need to find the key ID associated with this user and device
	// This would typically be fetched from our database
	keyID := "fetch_from_db" // Placeholder

	// Create a request to delete the key
	req, err := http.NewRequest("DELETE",
		fmt.Sprintf("%s/access-keys/%s", g.APIUrl, keyID), nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Authorization", "Bearer "+g.APIKey)

	resp, err := g.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("API returned non-success status: %d", resp.StatusCode)
	}

	return nil
}
