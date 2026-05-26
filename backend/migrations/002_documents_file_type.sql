-- Migration 002: Add file_type column to documents table
-- This tracks whether a document is a PDF or image (jpeg, png, webp)

ALTER TABLE documents ADD COLUMN file_type TEXT DEFAULT 'pdf';
