-- ============================================================
-- Pneumonia Detection System — Database Schema
-- MySQL 8.0+
-- Run: mysql -u root -p < database/schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS pneumonia_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE pneumonia_db;

-- ============================================================
-- Table: users
-- Stores registered user accounts
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id                INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    name              VARCHAR(100)    NOT NULL,
    email             VARCHAR(255)    NOT NULL,
    password_hash     VARCHAR(255)    NOT NULL,
    contact_number    VARCHAR(20)     NOT NULL,
    is_active         TINYINT(1)      NOT NULL DEFAULT 1,
    email_verified    TINYINT(1)      NOT NULL DEFAULT 0,
    verification_token VARCHAR(64)    NULL,
    created_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                      ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_users_email (email),
    INDEX idx_users_email (email),
    INDEX idx_users_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: prediction_logs
-- Stores every prediction made by users for audit & history
-- ============================================================
CREATE TABLE IF NOT EXISTS prediction_logs (
    id               INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    user_id          INT UNSIGNED    NOT NULL,
    image_filename   VARCHAR(255)    NOT NULL,
    image_path       VARCHAR(500)    NOT NULL,
    result           ENUM('NORMAL','PNEUMONIA') NOT NULL,
    confidence_score DECIMAL(6,4)    NULL COMMENT 'Value 0.0000 to 1.0000',
    model_used       ENUM('resnet50','mobilenetv2','custom_cnn')
                                     NOT NULL DEFAULT 'resnet50',
    precaution_text  TEXT            NULL,
    predicted_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_prediction_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    INDEX idx_prediction_user_id (user_id),
    INDEX idx_prediction_result (result),
    INDEX idx_prediction_predicted_at (predicted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
