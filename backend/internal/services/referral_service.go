package services

import (
	"errors"
	"time"

	"github.com/okoloboga/backend/internal/models"
	"github.com/okoloboga/backend/internal/repositories"
)

// ReferralService defines methods for referral-related operations
type ReferralService interface {
	AddReferral(userID int, referrerID int) error
	GetReferrals(userID int) ([]models.Referral, error)
	CountReferrals(referrerID int) (int64, error)
}

// referralService implements ReferralService
type referralService struct {
	referralRepo repositories.ReferralRepository
	userRepo     repositories.UserRepository
}

// NewReferralService creates a new referral service
func NewReferralService(
	referralRepo repositories.ReferralRepository,
	userRepo repositories.UserRepository,
) ReferralService {
	return &referralService{
		referralRepo: referralRepo,
		userRepo:     userRepo,
	}
}

// AddReferral adds a new referral
func (s *referralService) AddReferral(userID int, referrerID int) error {
	// Check if user exists
	_, err := s.userRepo.GetByID(userID)
	if err != nil {
		return errors.New("user not found")
	}

	// Check if referrer exists
	_, err = s.userRepo.GetByID(referrerID)
	if err != nil {
		return errors.New("referrer not found")
	}

	// Create new referral
	referral := &models.Referral{
		UserID:     userID,
		ReferrerID: referrerID,
		CreatedAt:  time.Now(),
	}

	if err := s.referralRepo.Create(referral); err != nil {
		return err
	}

	// Add bonus to referrer's balance (e.g., 100 units)
	const referralBonus = 100.0
	return s.userRepo.UpdateBalance(referrerID, referralBonus)
}

// GetReferrals retrieves all referrals for a user
func (s *referralService) GetReferrals(userID int) ([]models.Referral, error) {
	return s.referralRepo.GetByUserID(userID)
}

// CountReferrals counts the number of referrals for a user
func (s *referralService) CountReferrals(referrerID int) (int64, error) {
	return s.referralRepo.CountByReferrerID(referrerID)
}
