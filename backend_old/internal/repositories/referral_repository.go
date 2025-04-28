// internal/repositories/referral_repository.go
package repositories

import (
	"github.com/okoloboga/jeskovpn/backend/internal/models"
	"gorm.io/gorm"
)

// ReferralRepository defines methods for referral data access
type ReferralRepository interface {
	Create(referral *models.Referral) error
	GetByUserID(userID int) ([]models.Referral, error)
	CountByReferrerID(referrerID int) (int64, error)
}

// referralRepository implements ReferralRepository
type referralRepository struct {
	db *gorm.DB
}

// NewReferralRepository creates a new referral repository
func NewReferralRepository(db *gorm.DB) ReferralRepository {
	return &referralRepository{db: db}
}

// Create adds a new referral
func (r *referralRepository) Create(referral *models.Referral) error {
	return r.db.Create(referral).Error
}

// GetByUserID retrieves all referrals for a user
func (r *referralRepository) GetByUserID(userID int) ([]models.Referral, error) {
	var referrals []models.Referral
	result := r.db.Where("user_id = ?", userID).Find(&referrals)
	if result.Error != nil {
		return nil, result.Error
	}
	return referrals, nil
}

// CountByReferrerID counts referrals by referrer ID
func (r *referralRepository) CountByReferrerID(referrerID int) (int64, error) {
	var count int64
	err := r.db.Model(&models.Referral{}).
		Where("referrer_id = ?", referrerID).
		Count(&count).Error

	return count, err
}
